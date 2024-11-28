import pytest

from django_setup_configuration.exceptions import (
    ConfigurationException,
    PrerequisiteFailed,
    ValidateRequirementsFailure,
)
from django_setup_configuration.runner import (
    SetupConfigurationRunner,
    StepExecutionResult,
)
from django_setup_configuration.test_utils import execute_single_step
from tests.conftest import TestStep, TestStepConfig


def test_runner_raises_on_non_existent_step_module_path(test_step_yaml_path):
    with pytest.raises(ConfigurationException):
        SetupConfigurationRunner(
            steps=[TestStep, "module.does.not.exist"], yaml_source=test_step_yaml_path
        )


def test_runner_raises_on_passing_invalid_step_class(test_step_yaml_path):
    class NotABaseConfigurationStep:
        pass

    with pytest.raises(ConfigurationException):
        SetupConfigurationRunner(
            steps=[TestStep, NotABaseConfigurationStep], yaml_source=test_step_yaml_path
        )


def test_runner_raises_on_non_existent_yaml_path():
    with pytest.raises(ConfigurationException):
        SetupConfigurationRunner(
            steps=[TestStep], yaml_source="/does/not/exist/anywhere"
        )


def test_validate_requirements_for_step_fails_on_bad_yaml(
    runner_with_invalid_yaml, step_execute_mock, test_step_bad_yaml_path
):
    (step,) = runner_with_invalid_yaml.configured_steps
    with pytest.raises(PrerequisiteFailed):
        runner_with_invalid_yaml._validate_requirements_for_step(step)

    step_execute_mock.assert_not_called()


def test_validate_all_requirements_fails_on_bad_yaml(
    step_execute_mock,
    runner_with_invalid_yaml,
):
    with pytest.raises(ValidateRequirementsFailure) as excinfo:
        runner_with_invalid_yaml.validate_all_requirements()

    assert all(isinstance(exc, PrerequisiteFailed) for exc in excinfo.value.exceptions)

    step_execute_mock.assert_not_called()


def test_execute_step_returns_correct_result(
    step_execute_mock, expected_step_config, runner_step, test_step_yaml_path
):
    result = execute_single_step(TestStep, yaml_source=test_step_yaml_path)

    assert result == StepExecutionResult(
        step=result.step,
        is_enabled=True,
        has_run=True,
        run_exception=None,
        config_model=expected_step_config,
    )
    assert type(result.step) is TestStep
    step_execute_mock.assert_called_once_with(expected_step_config)


def test_execute_all_returns_correct_results(
    runner,
    step_execute_mock,
    expected_step_config,
):
    results = runner.execute_all()

    assert results == [
        StepExecutionResult(
            step=results[0].step,
            is_enabled=True,
            has_run=True,
            run_exception=None,
            config_model=expected_step_config,
        )
    ]
    assert type(results[0].step) is TestStep

    step_execute_mock.assert_called_once_with(expected_step_config)


def test_exception_during_execute_step_is_included_in_result(
    step_execute_mock,
    expected_step_config,
    runner,
):
    step_execute_mock.side_effect = Exception()
    (step,) = runner.configured_steps
    result = runner._execute_step(step)

    assert result == StepExecutionResult(
        step=result.step,
        is_enabled=True,
        has_run=True,
        run_exception=step_execute_mock.side_effect,
        config_model=expected_step_config,
    )
    assert type(result.step) is TestStep

    step_execute_mock.assert_called_once_with(expected_step_config)


def test_exception_during_execute_all_is_included_in_result(
    runner,
    step_execute_mock,
    expected_step_config,
):
    step_execute_mock.side_effect = Exception()
    results = runner.execute_all()

    assert results == [
        StepExecutionResult(
            step=results[0].step,
            is_enabled=True,
            has_run=True,
            run_exception=step_execute_mock.side_effect,
            config_model=expected_step_config,
        )
    ]
    assert type(results[0].step) is TestStep
    step_execute_mock.assert_called_once_with(expected_step_config)


def test_disabled_steps_are_not_run(
    runner_with_step_disabled_yaml,
    step_execute_mock,
):
    (step,) = runner_with_step_disabled_yaml.configured_steps
    result = runner_with_step_disabled_yaml._execute_step(step)

    assert result.is_enabled is False
    assert result == StepExecutionResult(
        step=result.step,
        is_enabled=False,
        has_run=False,
        run_exception=None,
        config_model=None,
    )
    assert type(result.step) is TestStep
    step_execute_mock.assert_not_called()


def test_disabled_steps_are_run_if_override_flag_is_provided(
    runner_with_step_disabled_yaml,
    step_execute_mock,
    expected_step_config,
):
    (step,) = runner_with_step_disabled_yaml.configured_steps
    result = runner_with_step_disabled_yaml._execute_step(step, ignore_enabled=True)

    assert result.is_enabled is False
    assert result == StepExecutionResult(
        step=result.step,
        is_enabled=False,
        has_run=True,
        run_exception=None,
        config_model=expected_step_config,
    )
    assert type(result.step) is TestStep
    step_execute_mock.assert_called_once_with(expected_step_config)


def test_settings_can_be_overriden_with_object(
    test_step_yaml_path, test_step_valid_config
):
    runner = SetupConfigurationRunner(
        steps=[TestStep],
        yaml_source=test_step_yaml_path,
        object_source={
            "test_step": {
                "username": "overriden username",
            },
        },
    )
    (step,) = runner.configured_steps

    assert runner._validate_requirements_for_step(
        step
    ) == TestStepConfig.model_validate(
        test_step_valid_config["test_step"]
        | {
            "username": "overriden username",
        },
    )
