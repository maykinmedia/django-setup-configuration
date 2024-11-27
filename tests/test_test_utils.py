import pytest

from django_setup_configuration.runner import StepExecutionResult
from django_setup_configuration.test_utils import execute_single_step
from tests.conftest import TestStep


def test_exception_during_execute_step_is_immediately_raised(
    step_execute_mock,
    test_step_yaml_path,
    expected_step_config,
):
    step_execute_mock.side_effect = Exception("the error")
    with pytest.raises(Exception) as excinfo:
        execute_single_step(TestStep, yaml_source=test_step_yaml_path)

    assert str(excinfo.value) == "the error"

    step_execute_mock.assert_called_once_with(expected_step_config)


def test_execute_single_step_returns_result_if_no_exceptions(
    step_execute_mock,
    test_step_yaml_path,
    expected_step_config,
):
    result = execute_single_step(TestStep, yaml_source=test_step_yaml_path)

    assert result == StepExecutionResult(
        step=result.step,
        is_enabled=True,
        has_run=True,
        run_exception=None,
        config_model=expected_step_config,
    )
    assert isinstance(result.step, TestStep)

    step_execute_mock.assert_called_once_with(expected_step_config)


def test_execute_single_step_ignores_enabled_setting(
    step_execute_mock,
    test_step_yaml_path,
    expected_step_config,
):
    result = execute_single_step(
        TestStep,
        yaml_source=test_step_yaml_path,
        object_source={"test_step_is_enabled": False},
    )

    assert result == StepExecutionResult(
        step=result.step,
        is_enabled=False,
        has_run=True,
        run_exception=None,
        config_model=expected_step_config,
    )
    assert isinstance(result.step, TestStep)
    step_execute_mock.assert_called_once_with(expected_step_config)
