from io import StringIO

from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.management import CommandError, call_command

import pytest

from django_setup_configuration.contrib.sites.steps import SitesConfigurationStep
from django_setup_configuration.test_utils import execute_single_step

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def include_test_step(settings):
    settings.SETUP_CONFIGURATION_STEPS = settings.SETUP_CONFIGURATION_STEPS + [
        SitesConfigurationStep
    ]


CONFIG_FILE_PATH = "tests/sites/files/sites.yaml"
CONFIG_FILE_PATH_INVALID = "tests/sites/files/sites_invalid.yaml"


@pytest.mark.django_db
def test_execute_configuration_step_success():
    # should be updated by the step
    Site.objects.get_or_create(domain="example.com", defaults={"name": "example"})

    execute_single_step(SitesConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    assert Site.objects.count() == 2

    site1, site2 = Site.objects.all()

    assert site1.domain == "domain.local1:8000"
    assert site1.name == "Domain1"
    assert site2.domain == "domain.local2:8000"
    assert site2.name == "Domain2"
    assert Site.objects.get_current() == site1


@pytest.mark.django_db
def test_execute_configuration_step_update_existing():
    Site.objects.create(name="old", domain="domain.local2:8000")

    execute_single_step(SitesConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    assert Site.objects.count() == 2

    site1, site2 = Site.objects.all()

    assert site1.domain == "domain.local1:8000"
    assert site1.name == "Domain1"
    assert site2.domain == "domain.local2:8000"
    assert site2.name == "Domain2"

    assert Site.objects.get_current() == site1


@pytest.mark.django_db
def test_execute_configuration_step_idempotent():
    def make_assertions():
        assert Site.objects.count() == 2

        site1, site2 = Site.objects.all()

        assert site1.domain == "domain.local1:8000"
        assert site1.name == "Domain1"
        assert site2.domain == "domain.local2:8000"
        assert site2.name == "Domain2"

        assert Site.objects.get_current() == site1

    execute_single_step(SitesConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    make_assertions()

    execute_single_step(SitesConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    make_assertions()


@pytest.mark.django_db
def test_execute_configuration_step_failing_should_keep_existing_sites():
    site, _ = Site.objects.get_or_create(
        domain="example.com", defaults={"name": "example"}
    )

    with pytest.raises(ValidationError):
        execute_single_step(
            SitesConfigurationStep, yaml_source=CONFIG_FILE_PATH_INVALID
        )

    assert Site.objects.count() == 1
    assert Site.objects.get() == site


@pytest.mark.django_db
def test_execute_configuration_step_creates_a_current_site_if_no_sites_exist():
    Site.objects.all().delete()

    execute_single_step(SitesConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    site1, site2 = Site.objects.all()

    assert site1.domain == "domain.local1:8000"
    assert site1.name == "Domain1"
    assert site2.domain == "domain.local2:8000"
    assert site2.name == "Domain2"
    assert Site.objects.get_current() == site1


@pytest.fixture()
def empty_site_id_in_settings(settings):
    settings.SITE_ID = None


@pytest.mark.usefixtures("empty_site_id_in_settings")
@pytest.mark.django_db
def test_execute_configuration_step_creates_a_current_site_if_no_sites_or_site_id():
    Site.objects.all().delete()

    execute_single_step(SitesConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    site1, site2 = Site.objects.all()

    assert site1.domain == "domain.local1:8000"
    assert site1.name == "Domain1"
    assert site2.domain == "domain.local2:8000"
    assert site2.name == "Domain2"

    # There is no SITE_ID defined. We should still have created the Sites, but there is
    # no default defined, so `get_current()` will not work without passing a request
    # (which would allow Django to match on the host).
    with pytest.raises(ImproperlyConfigured):
        Site.objects.get_current()


def test_command_reports_validation_error():
    stdout, stderr = StringIO(), StringIO()

    with pytest.raises(CommandError) as excinfo:
        call_command(
            "setup_configuration",
            yaml_file=CONFIG_FILE_PATH_INVALID,
            stdout=stdout,
            stderr=stderr,
        )

    assert (
        "Error while executing step `Sites configuration`\n    {'domain': ['The domain"
        " name cannot contain any spaces or tabs.']}\n" in stderr.getvalue()
    )
    assert (
        str(excinfo.value)
        == "Aborting run due to a failed step. All database changes have been rolled "
        "back."
    )
