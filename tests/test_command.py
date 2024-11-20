from io import StringIO

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command

import pytest

from django_setup_configuration.test_utils import build_step_config_from_sources
from testapp.configuration import UserConfigurationModel, UserConfigurationStep
from tests.conftest import TestStep

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def include_test_step(settings):
    settings.SETUP_CONFIGURATION_STEPS = settings.SETUP_CONFIGURATION_STEPS + [TestStep]


@pytest.fixture()
def user_config_model():
    return UserConfigurationModel(username="demo", password="secret")


@pytest.fixture()
def yaml_file_with_valid_configuration(yaml_file_factory, test_step_valid_config):
    yaml_path = yaml_file_factory(
        {
            "user_configuration_enabled": True,
            "user_configuration": {
                "username": "demo",
                "password": "secret",
            },
            "some_extra_attrs": "should be allowed",
        }
        | test_step_valid_config
    )

    return yaml_path


@pytest.fixture()
def yaml_file_with_invalid_configuration(yaml_file_factory, test_step_valid_config):
    yaml_path = yaml_file_factory(
        {
            "user_configuration_enabled": True,
            "user_configuration": {
                "username": "demo",
                "password": "secret",
            },
            "some_extra_attrs": "should be allowed",
        }
        | test_step_valid_config
    )

    return yaml_path


def test_command_errors_on_missing_yaml_file(step_execute_mock):
    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration",
        )

    assert str(exc.value) == (
        "Error: the following arguments are required: --yaml-file"
    )
    step_execute_mock.assert_not_called()


def test_command_errors_on_no_configured_steps(
    settings, step_execute_mock, yaml_file_with_valid_configuration
):
    settings.SETUP_CONFIGURATION_STEPS = None

    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration", yaml_file=yaml_file_with_valid_configuration
        )

    assert str(exc.value) == (
        "You must provide one or more steps, or configure "
        "these steps via `settings.SETUP_CONFIGURATION_STEPS`"
    )
    step_execute_mock.assert_not_called()


def test_command_errors_on_no_enabled_steps(step_execute_mock, yaml_file_factory):
    yaml_file_path = yaml_file_factory(
        {
            "test_step_is_enabled": False,
            "user_configuration_enabled": False,
        }
    )
    with pytest.raises(CommandError) as exc:
        call_command("setup_configuration", yaml_file=yaml_file_path)

    assert str(exc.value) == "No steps enabled, aborting."
    step_execute_mock.assert_not_called()


def test_command_errors_on_bad_yaml_file(step_execute_mock):
    with pytest.raises(CommandError) as exc:
        call_command("setup_configuration", yaml_file="/does/not/exist")

    assert str(exc.value) == "Yaml file `/does/not/exist` does not exist."
    step_execute_mock.assert_not_called()


def test_command_success(
    settings,
    yaml_file_with_valid_configuration,
    expected_step_config,
    step_execute_mock,
):
    """
    test happy flow
    """
    assert User.objects.count() == 0
    stdout = StringIO()

    call_command(
        "setup_configuration",
        yaml_file=yaml_file_with_valid_configuration,
        stdout=stdout,
    )

    output = stdout.getvalue().splitlines()
    expected_output = [
        f"Loading config settings from {yaml_file_with_valid_configuration}",
        "The following steps are configured:",
        "User Configuration",
        "TestStep",
        "Executing steps...",
        "Successfully executed step: User Configuration",
        "Successfully executed step: TestStep",
        "Instance configuration completed.",
    ]

    assert output == expected_output

    assert User.objects.count() == 1
    user = User.objects.get()
    assert user.username == "demo"
    assert user.check_password("secret") is True

    step_execute_mock.assert_called_once_with(expected_step_config)


def test_command_with_failing_requirements_reports_errors(
    step_execute_mock, yaml_file_factory
):
    yaml_path = yaml_file_factory(
        {
            "user_configuration_enabled": True,
            "user_configuration": {
                "username": 1874,
            },
            "some_extra_attrs": "should be allowed",
            "test_step_is_enabled": True,
            "test_step": {
                "a_string": 42,
                "username": None,
            },
        }
    )

    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration",
            yaml_file=yaml_path,
        )

    assert (
        "User Configuration: Failed to load config model for User Configuration"
        in str(exc.value)
    )
    assert "Failed to load config model for TestStep" in str(exc.value)

    assert User.objects.count() == 0
    step_execute_mock.assert_not_called()


def test_command_with_failing_execute_reports_errors(
    expected_step_config, step_execute_mock, yaml_file_with_valid_configuration
):
    step_execute_mock.side_effect = ValueError("Something went wrong")

    stdout = StringIO()

    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration",
            stdout=stdout,
            yaml_file=yaml_file_with_valid_configuration,
        )

    assert (
        str(exc.value) == "Error while executing step `TestStep`: Something went wrong"
    )

    output = stdout.getvalue().splitlines()
    expected_output = [
        f"Loading config settings from {yaml_file_with_valid_configuration}",
        "The following steps are configured:",
        "User Configuration",
        "TestStep",
        "Executing steps...",
        "Successfully executed step: User Configuration",
    ]

    assert output == expected_output

    assert User.objects.count() == 0
    step_execute_mock.assert_called_once_with(expected_step_config)


def test_load_step_config_from_source_returns_correct_model(
    yaml_file_with_valid_configuration, user_config_model
):
    model = build_step_config_from_sources(
        UserConfigurationStep, yaml_file_with_valid_configuration
    )

    assert model == user_config_model
