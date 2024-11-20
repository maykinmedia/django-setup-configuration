import pytest

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationException
from django_setup_configuration.models import ConfigurationModel


@pytest.mark.parametrize(
    "required_attribute",
    (
        "verbose_name",
        "config_model",
        "namespace",
        "enable_setting",
    ),
)
def test_constructor_raises_upon_missing_required_fields(required_attribute):
    class FooModel(ConfigurationModel):
        foo: str

    class Foo(BaseConfigurationStep):

        verbose_name = "Verbose Name"
        config_model = FooModel
        namespace = "Namespace"
        enable_setting = "Enable setting"

        def is_configured(self, model) -> bool:
            pass

        def execute(self, model) -> None:
            pass

        def validate_result(self, model) -> None:
            pass

    delattr(Foo, required_attribute)
    with pytest.raises(ConfigurationException):
        Foo()
