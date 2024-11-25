from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from django_setup_configuration.exceptions import ConfigurationException
from django_setup_configuration.models import ConfigurationModel

TConfigModel = TypeVar("TConfigModel", bound=ConfigurationModel)


class BaseConfigurationStep(ABC, Generic[TConfigModel]):
    """
    A single configuration step to configure some part of the Django application.

    Attributes:
        enable_setting (`str`): the setting for enabling the associated configuration
            step
        config_model (`ConfigurationModel`): a list of `ConfigField` objects containing
            information about Django model fields
        namespace (`str`): the namespace of configuration variables for a given
            configuration

    Example:
        ```python
        class FooConfiguration(ConfigurationModel):
            some_setting: str

        class FooConfigurationStep(BaseConfigurationStep):
            verbose_name = "Configuration step for Foo"
            enable_setting = "foo_config_enable"
            namespace="foo"

        @abstractmethod
        def execute(self, model) -> None:
            SomeModel.objects.create(foo=model.some_setting)

        ```
    """

    verbose_name: str
    config_model: type[TConfigModel]
    namespace: str
    enable_setting: str

    def __init__(self):
        for attr in (
            "verbose_name",
            "config_model",
            "namespace",
            "enable_setting",
        ):
            if not getattr(self, attr, None):
                raise ConfigurationException(
                    f"You must set {self.__class__.__name__}.{attr}"
                )

    def __repr__(self):
        return self.verbose_name

    @abstractmethod
    def execute(self, model: TConfigModel) -> None:
        """
        Run the configuration step.

        :raises: :class: `django_setup_configuration.exceptions.ConfigurationRunFailed`
        if the configuration has an error
        """
        ...
