from django.core.management import call_command

import pytest

from django_setup_configuration.exceptions import ImproperlyConfigured
from django_setup_configuration.registry import ConfigurationRegistry
from testapp.configuration import ProductConfigurationSettings


def test_missing_registry(settings):
    del settings.DJANGO_SETUP_CONFIG_REGISTER

    with pytest.raises(ImproperlyConfigured):
        call_command("generate_config_docs")


def test_registry_missing_model_spec(settings):
    settings.DJANGO_SETUP_CONFIG_REGISTER = [{"file_name": "test"}]

    with pytest.raises(ImproperlyConfigured):
        call_command("generate_config_docs")


def test_registry_model_not_found(settings):
    settings.DJANGO_SETUP_CONFIG_REGISTER = [{"model": "testapp.models.bogus"}]

    with pytest.raises(ImproperlyConfigured):
        call_command("generate_config_docs")


def test_registry_property_models():
    registry = ConfigurationRegistry()

    models = registry.config_models

    assert len(models) == 1
    assert models[0] == ProductConfigurationSettings


def test_registry_property_model_keys():
    registry = ConfigurationRegistry()

    model_keys = registry.config_model_keys

    assert len(model_keys) == 1
    assert model_keys[0] == "product"
