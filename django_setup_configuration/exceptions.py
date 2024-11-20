from typing import TYPE_CHECKING

from pydantic import ValidationError

if TYPE_CHECKING:
    from django_setup_configuration.configuration import BaseConfigurationStep


class ConfigurationException(Exception):
    """
    Base exception for configuration steps
    """


class PrerequisiteFailed(ConfigurationException):
    """
    Raises an error when the configuration step can't be started
    """

    step: "BaseConfigurationStep"
    validation_error: ValidationError

    def __init__(
        self, step: "BaseConfigurationStep", validation_error: ValidationError
    ):
        self.step = step
        self.validation_error = validation_error
        super().__init__(
            f"Failed to load config model for {step}. Further "
            f"details:\n{str(validation_error)}"
        )


class ConfigurationRunFailed(ConfigurationException):
    """
    Raises an error when the configuration process was faulty
    """

    pass


class ImproperlyConfigured(ConfigurationException):
    """
    Raised when the library is not properly configured
    """


class ValidateRequirementsFailure(ConfigurationException):
    """
    Container exception for one or more failed step requirements
    """

    exceptions: list[PrerequisiteFailed]

    def __init__(self, exceptions: list[PrerequisiteFailed]):
        self.exceptions = exceptions
        super().__init__(
            "One or more steps were provided with incomplete or incorrect settings"
        )
