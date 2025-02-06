from io import StringIO

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command

import pydantic
import pytest

from django_setup_configuration.test_utils import build_step_config_from_sources
from testapp.configuration import UserConfigurationModel, UserConfigurationStep
from tests.conftest import ConfigStep

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def include_test_step(settings):
    settings.SETUP_CONFIGURATION_STEPS = settings.SETUP_CONFIGURATION_STEPS + [
        ConfigStep
    ]


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


def test_command_errors_on_step_instance_rather_than_class(
    settings, step_execute_mock, yaml_file_with_valid_configuration
):
    settings.SETUP_CONFIGURATION_STEPS = [ConfigStep()]

    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration", yaml_file=yaml_file_with_valid_configuration
        )

    assert str(exc.value) == (
        "Your configured steps contain `ConfigStep`, which is not a class: "
        "did you perhaps provide an instance?"
    )
    step_execute_mock.assert_not_called()


def test_command_errors_on_step_which_does_not_inherit_from_base_configuration_step(
    settings, step_execute_mock, yaml_file_with_valid_configuration
):
    class Foo:
        pass

    settings.SETUP_CONFIGURATION_STEPS = [Foo]

    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration", yaml_file=yaml_file_with_valid_configuration
        )

    assert str(exc.value) == (
        "Your configured steps contain Foo` which is not "
        "a subclass of `BaseConfigurationStep`"
    )
    step_execute_mock.assert_not_called()


def test_command_errors_on_non_importable_configuration_Step(
    settings, step_execute_mock, yaml_file_with_valid_configuration
):
    settings.SETUP_CONFIGURATION_STEPS = ["this.module.does.not.exist"]

    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration", yaml_file=yaml_file_with_valid_configuration
        )

    assert str(exc.value) == (
        "Your configured steps contain `this.module.does.not.exist`, which "
        "cannot be imported"
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
    yaml_file_with_valid_configuration,
    expected_step_config,
    step_execute_mock,
):
    """
    test happy flow
    """
    assert User.objects.count() == 0
    stdout, stderr = StringIO(), StringIO()

    call_command(
        "setup_configuration",
        yaml_file=yaml_file_with_valid_configuration,
        stdout=stdout,
        stderr=stderr,
    )

    assert stderr.getvalue() == ""

    # flake8: noqa: E501
    output = stdout.getvalue().splitlines()
    expected_output = [
        f"Loading config settings from {yaml_file_with_valid_configuration}",
        "The following steps are configured:",
        "    User Configuration from <class 'testapp.configuration.UserConfigurationStep'> [enabled]",
        "    ConfigStep from <class 'tests.conftest.ConfigStep'> [enabled]",
        "",
        "Validating requirements...",
        "Valid configuration settings found for all steps.",
        "",
        "Executing steps...",
        "    Successfully executed step: User Configuration",
        "    Successfully executed step: ConfigStep",
        "",
        "Configuration completed.",
    ]
    # flake8: qa: E501

    assert output == expected_output

    assert User.objects.count() == 1
    user = User.objects.get()
    assert user.username == "demo"
    assert user.check_password("secret") is True

    step_execute_mock.assert_called_once_with(expected_step_config)


def test_command_success_with_validate_only_flag_does_not_run(
    settings,
    yaml_file_with_valid_configuration,
    expected_step_config,
    step_execute_mock,
):
    stdout, stderr = StringIO(), StringIO()

    call_command(
        "setup_configuration",
        yaml_file=yaml_file_with_valid_configuration,
        validate_only=True,
        stdout=stdout,
        stderr=stderr,
    )

    output = stdout.getvalue().splitlines()
    expected_output = [
        f"Loading config settings from {yaml_file_with_valid_configuration}",
        "The following steps are configured:",
        "    User Configuration from <class 'testapp.configuration.UserConfigurationStep'> [enabled]",
        "    ConfigStep from <class 'tests.conftest.ConfigStep'> [enabled]",
        "",
        "Validating requirements...",
        "Valid configuration settings found for all steps.",
    ]

    assert output == expected_output

    assert User.objects.count() == 0
    step_execute_mock.assert_not_called()


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

    stdout, stderr = StringIO(), StringIO()
    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration",
            yaml_file=yaml_path,
            stdout=stdout,
            stderr=stderr,
        )

    assert "Failed to validate requirements for 2 steps" in str(exc.value)

    output = stderr.getvalue().splitlines()

    # Strip the patch version, which is not used in the URLs
    pydantic_version = ".".join(pydantic.__version__.split(".")[:2])
    # flake8: noqa: E501
    expected_output = [
        'Invalid configuration settings for step "User Configuration":',
        "    2 validation errors for ConfigSettingsSourceUser_configuration",
        "    user_configuration.username",
        "      Input should be a valid string [type=string_type, input_value=1874, input_type=int]",
        f"        For further information visit https://errors.pydantic.dev/{pydantic_version}/v/string_type",
        "    user_configuration.password",
        "      Field required [type=missing, input_value={'username': 1874}, input_type=dict]",
        f"        For further information visit https://errors.pydantic.dev/{pydantic_version}/v/missing",
        "",
        'Invalid configuration settings for step "ConfigStep":',
        "    2 validation errors for ConfigSettingsSourceTest_step",
        "    test_step.a_string",
        "      Input should be a valid string [type=string_type, input_value=42, input_type=int]",
        f"        For further information visit https://errors.pydantic.dev/{pydantic_version}/v/string_type",
        "    test_step.username",
        "      Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]",
        f"        For further information visit https://errors.pydantic.dev/{pydantic_version}/v/string_type",
        "",
    ]

    assert output == expected_output

    output = stdout.getvalue().splitlines()
    expected_output = [
        f"Loading config settings from {yaml_path}",
        "The following steps are configured:",
        "    User Configuration from <class 'testapp.configuration.UserConfigurationStep'> [enabled]",
        "    ConfigStep from <class 'tests.conftest.ConfigStep'> [enabled]",
        "",
        "Validating requirements...",
    ]
    # flake8: qa: E501

    assert output == expected_output

    assert User.objects.count() == 0
    step_execute_mock.assert_not_called()


def test_command_with_failing_requirements_and_validate_reports_errors(
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

    stdout, stderr = StringIO(), StringIO()
    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration",
            yaml_file=yaml_path,
            validate_only=False,
            stdout=stdout,
            stderr=stderr,
        )

    output = stderr.getvalue().splitlines()

    # Strip the patch version, which is not used in the URLs
    pydantic_version = ".".join(pydantic.__version__.split(".")[:2])
    # flake8: noqa: E501
    expected_output = [
        'Invalid configuration settings for step "User Configuration":',
        "    2 validation errors for ConfigSettingsSourceUser_configuration",
        "    user_configuration.username",
        "      Input should be a valid string [type=string_type, input_value=1874, input_type=int]",
        f"        For further information visit https://errors.pydantic.dev/{pydantic_version}/v/string_type",
        "    user_configuration.password",
        "      Field required [type=missing, input_value={'username': 1874}, input_type=dict]",
        f"        For further information visit https://errors.pydantic.dev/{pydantic_version}/v/missing",
        "",
        'Invalid configuration settings for step "ConfigStep":',
        "    2 validation errors for ConfigSettingsSourceTest_step",
        "    test_step.a_string",
        "      Input should be a valid string [type=string_type, input_value=42, input_type=int]",
        f"        For further information visit https://errors.pydantic.dev/{pydantic_version}/v/string_type",
        "    test_step.username",
        "      Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]",
        f"        For further information visit https://errors.pydantic.dev/{pydantic_version}/v/string_type",
        "",
    ]

    assert output == expected_output

    output = stdout.getvalue().splitlines()
    expected_output = [
        f"Loading config settings from {yaml_path}",
        "The following steps are configured:",
        "    User Configuration from <class 'testapp.configuration.UserConfigurationStep'> [enabled]",
        "    ConfigStep from <class 'tests.conftest.ConfigStep'> [enabled]",
        "",
        "Validating requirements...",
    ]
    assert output == expected_output
    # flake8: qa: E501

    assert User.objects.count() == 0
    step_execute_mock.assert_not_called()


def test_command_with_failing_execute_reports_errors(
    expected_step_config, step_execute_mock, yaml_file_with_valid_configuration
):
    step_execute_mock.side_effect = ValueError("Something went wrong")

    stdout, stderr = StringIO(), StringIO()

    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration",
            yaml_file=yaml_file_with_valid_configuration,
            stdout=stdout,
            stderr=stderr,
        )

    # flake8: noqa: E501
    assert (
        str(exc.value)
        == "Aborting run due to a failed step. All database changes have been rolled back."
    )

    output = stdout.getvalue().splitlines()
    expected_output = [
        f"Loading config settings from {yaml_file_with_valid_configuration}",
        "The following steps are configured:",
        "    User Configuration from <class 'testapp.configuration.UserConfigurationStep'> [enabled]",
        "    ConfigStep from <class 'tests.conftest.ConfigStep'> [enabled]",
        "",
        "Validating requirements...",
        "Valid configuration settings found for all steps.",
        "",
        "Executing steps...",
        "    Successfully executed step: User Configuration",
    ]
    # flake8: qa: E501

    assert output == expected_output

    output = stderr.getvalue().splitlines()
    expected_output = [
        "Error while executing step `ConfigStep`",
        "    Something went wrong",
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


def test_command_aborts_on_no_enabled_steps(step_execute_mock, yaml_file_factory):
    yaml_path = yaml_file_factory(
        {
            "user_configuration_enabled": False,
            "test_step_is_enabled": False,
        }
    )

    stdout, stderr = StringIO(), StringIO()
    with pytest.raises(CommandError) as exc:
        call_command(
            "setup_configuration",
            yaml_file=yaml_path,
            stdout=stdout,
            stderr=stderr,
        )

    assert str(exc.value) == "No steps enabled, aborting."

    output = stdout.getvalue().splitlines()
    # flake8: noqa: E501
    expected_output = [
        f"Loading config settings from {yaml_path}",
        "The following steps are configured:",
        "    User Configuration from <class 'testapp.configuration.UserConfigurationStep'> [***disabled***]",
        "    ConfigStep from <class 'tests.conftest.ConfigStep'> [***disabled***]",
    ]
    # flake8: qa: E501

    assert output == expected_output

    assert stderr.getvalue() == ""

    assert User.objects.count() == 0
    step_execute_mock.assert_not_called()


def test_command_with_disabled_and_enabled_steps_lists_the_disabled_steps(
    step_execute_mock, yaml_file_factory
):
    yaml_path = yaml_file_factory(
        {
            "user_configuration_enabled": True,
            "user_configuration": {
                "username": "alice",
                "password": "secret",
            },
            "test_step_is_enabled": False,
        }
    )

    stdout, stderr = StringIO(), StringIO()
    call_command(
        "setup_configuration",
        yaml_file=yaml_path,
        stdout=stdout,
        stderr=stderr,
    )

    # flake8: noqa: E501
    output = stdout.getvalue().splitlines()
    expected_output = [
        f"Loading config settings from {yaml_path}",
        "The following steps are configured:",
        "    User Configuration from <class 'testapp.configuration.UserConfigurationStep'> [enabled]",
        "    ConfigStep from <class 'tests.conftest.ConfigStep'> [***disabled***]",
        "The following steps will be skipped because they are disabled:",
        "    ConfigStep from <class 'tests.conftest.ConfigStep'> [test_step_is_enabled = false]",
        "",
        "Validating requirements...",
        "Valid configuration settings found for all steps.",
        "",
        "Executing steps...",
        "    Successfully executed step: User Configuration",
        "",
        "Configuration completed.",
    ]
    # flake8: qa: E501

    assert output == expected_output
    assert stderr.getvalue() == ""

    assert User.objects.count() == 1
    step_execute_mock.assert_not_called()


@pytest.fixture()
def valid_config_object(test_step_valid_config):
    return {
        "transaction_test_configuration_enabled": True,
        "transaction_test_configuration": {"username": "alice"},
    } | test_step_valid_config


def test_command_rolls_back_all_on_failing_step(
    yaml_file_with_valid_configuration, step_execute_mock
):
    exc = Exception()
    step_execute_mock.side_effect = exc

    assert User.objects.count() == 0
    stdout, stderr = StringIO(), StringIO()

    with pytest.raises(CommandError) as excinfo:
        call_command(
            "setup_configuration",
            yaml_file=yaml_file_with_valid_configuration,
            stdout=stdout,
            stderr=stderr,
        )

    assert (
        str(excinfo.value)
        == "Aborting run due to a failed step. All database changes have been rolled back."
    )
    step_execute_mock.assert_called_once()

    # Initial run is rolled back, so no objects created
    assert User.objects.count() == 0

    # Subsequent run does not raise, so the objects are created
    step_execute_mock.side_effect = None

    call_command(
        "setup_configuration",
        yaml_file=yaml_file_with_valid_configuration,
        stdout=stdout,
        stderr=stderr,
    )
    assert User.objects.count() == 1
    assert step_execute_mock.call_count == 2
