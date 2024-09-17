from abc import ABC, abstractmethod

from django.conf import settings

from .config_settings import ConfigSettings
from .exceptions import PrerequisiteFailed


class BaseConfigurationStep(ABC):
    verbose_name: str
    config_settings: ConfigSettings

    def __repr__(self):
        return self.verbose_name

    def validate_requirements(self) -> None:
        """
        check prerequisites of the configuration

        :raises: :class: `django_setup_configuration.exceptions.PrerequisiteFailed`
        if prerequisites are missing
        """
        missing = [
            var
            for var in self.config_settings.required_settings
            if getattr(settings, var, None) in [None, ""]
        ]
        if missing:
            raise PrerequisiteFailed(
                f"{', '.join(missing)} settings should be provided"
            )

    def is_enabled(self) -> bool:
        """
        Hook to switch on and off the configuration step from env vars

        By default all steps are disabled
        """
        if not self.config_settings.enable_setting:
            return True

        return getattr(settings, self.config_settings.enable_setting, False) or False

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check that the configuration is already done with current env variables
        """
        ...

    @abstractmethod
    def configure(self) -> None:
        """
        Run the configuration step.

        :raises: :class: `django_setup_configuration.exceptions.ConfigurationRunFailed`
        if the configuration has an error
        """
        ...

    @abstractmethod
    def test_configuration(self) -> None:
        """
        Test that the configuration works as expected

        :raises: :class:`openzaak.config.bootstrap.exceptions.SelfTestFailure`
        if the configuration aspect was found to be faulty.
        """
        ...
