from typing import Any

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.runner import (
    SetupConfigurationRunner,
    StepExecutionResult,
)


def build_step_config_from_sources(
    step: type[BaseConfigurationStep[Any]] | str,
    yaml_source: str | None = None,
    object_source: dict | None = None,
):
    """
    Build a step's configuration model from YAML or object sources.

    Args:
        step: The configuration step class or step name to load and validate
        yaml_source: Optional path to a YAML configuration file
        object_source: Optional dictionary containing configuration settings

    Returns:
        Validated configuration model for the specified step

    Raises:
        `PrerequisiteFailed`: If configuration validation fails
    """
    runner = SetupConfigurationRunner(
        steps=[step],
        yaml_source=yaml_source,
        object_source=object_source,
    )
    return runner._validate_requirements_for_step(runner.configured_steps[0])


def execute_single_step(
    step: type[BaseConfigurationStep] | str,
    *,
    yaml_source: str | None = None,
    object_source: dict | None = None,
) -> StepExecutionResult:
    """
    Execute a single BaseConfigurationStep from YAML or object sources.

    Args:
        step (type[BaseConfigurationStep] | str): The configuration step class or step
            name to load and validate
        yaml_source (str | None, optional): Optional path to a YAML configuration file.
            Defaults to None.
        object_source (dict | None, optional): Optional dictionary containing
            configuration settings. Defaults to None.

    Returns:
        StepExecutionResult: The result of the step execution, including the validated
            model and any errors, if applicable.
    """
    runner = SetupConfigurationRunner(
        steps=[step],
        yaml_source=yaml_source,
        object_source=object_source,
    )
    result = runner._execute_step(runner.configured_steps[0], ignore_enabled=True)
    if result.run_exception:
        raise result.run_exception

    return result
