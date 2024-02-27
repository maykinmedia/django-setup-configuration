from io import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command

import pytest

from testapp.configuration import UserConfigurationStep

pytestmark = pytest.mark.django_db


def test_command_success():
    """
    test happy flow
    """
    assert User.objects.count() == 0

    stdout = StringIO()
    call_command("setup_configuration", stdout=stdout)

    output = stdout.getvalue().splitlines()
    step = UserConfigurationStep()
    expected_output = [
        f"Configuration will be set up with following steps: [{step}]",
        f"Configuring {step}...",
        f"{step} is successfully configured",
        "Instance configuration completed.",
    ]
    assert output == expected_output

    assert User.objects.count() == 1
    user = User.objects.get()
    assert user.username == settings.USER_CONFIGURATION_USERNAME
    assert user.check_password(settings.USER_CONFIGURATION_PASSWORD) is True


def test_command_called_twice(settings):
    """
    test that the second run doesn't change configuration
    """
    # 1st call
    settings.USER_CONFIGURATION_PASSWORD = "secret1"
    call_command("setup_configuration")
    user = User.objects.get(username=settings.USER_CONFIGURATION_USERNAME)
    assert user.check_password("secret1") is True

    # 2nd call
    settings.USER_CONFIGURATION_PASSWORD = "secret2"
    stdout = StringIO()
    call_command("setup_configuration", stdout=stdout)

    output = stdout.getvalue().splitlines()
    step = UserConfigurationStep()
    expected_output = [
        f"Configuration will be set up with following steps: [{step}]",
        f"Step {step} is skipped, because the configuration already exists.",
        "Instance configuration completed.",
    ]
    assert output == expected_output

    user = User.objects.get(username=settings.USER_CONFIGURATION_USERNAME)
    assert user.check_password("secret1") is True


def test_command_called_twice_with_overwrite():
    """
    test that the second run change configuration in overwrite mode
    """
    # 1st call
    settings.USER_CONFIGURATION_PASSWORD = "secret1"
    call_command("setup_configuration")
    user = User.objects.get(username=settings.USER_CONFIGURATION_USERNAME)
    assert user.check_password("secret1") is True

    # 2nd call
    settings.USER_CONFIGURATION_PASSWORD = "secret2"
    stdout = StringIO()
    call_command("setup_configuration", overwrite=True, stdout=stdout)

    output = stdout.getvalue().splitlines()
    step = UserConfigurationStep()
    expected_output = [
        f"Configuration will be set up with following steps: [{step}]",
        f"Configuring {step}...",
        f"{step} is successfully configured",
        "Instance configuration completed.",
    ]
    assert output == expected_output

    user = User.objects.get(username=settings.USER_CONFIGURATION_USERNAME)
    assert user.check_password("secret2") is True


def test_command_no_config_steps(settings):
    """
    test that the command quits in the beginning with appropriate stdout
    """
    settings.SETUP_CONFIGURATION_STEPS = []

    stdout = StringIO()
    call_command("setup_configuration", stdout=stdout)

    output = stdout.getvalue().splitlines()
    expected_output = [
        "There are no enabled configuration steps. Configuration can't be set up",
    ]
    assert output == expected_output
    assert User.objects.count() == 0


def test_command_disabled(settings):
    """
    test that the command doesn't run the disabled configuration step
    """
    settings.USER_CONFIGURATION_ENABLED = False

    stdout = StringIO()
    call_command("setup_configuration", stdout=stdout)

    output = stdout.getvalue().splitlines()
    expected_output = [
        "There are no enabled configuration steps. Configuration can't be set up",
    ]
    assert output == expected_output
    assert User.objects.count() == 0


def test_command_failed_selftest(mocker):
    """
    test that if configuration.test_configuration fails with SelfTestFailed
    CommandError is raised and no db change is done
    """
    mocker.patch("testapp.configuration.authenticate", return_value=None)

    with pytest.raises(CommandError) as exc:
        call_command("setup_configuration")

    exc_description = (
        f"Configuration test failed with errors: "
        f"{UserConfigurationStep()}: No user with provided credentials is found"
    )
    assert exc.value.args[0] == exc_description
    assert User.objects.count() == 0


def test_command_skip_selftest(mocker):
    """
    test that command skips selftest
    """
    stdout = StringIO()
    mocker.patch("testapp.configuration.authenticate", return_value=None)

    call_command("setup_configuration", no_selftest=True, stdout=stdout)

    output = stdout.getvalue()
    assert "Selftest is skipped." in output
