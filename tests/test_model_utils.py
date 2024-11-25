import pytest
from pydantic import ValidationError

from django_setup_configuration.model_utils import create_config_source_models
from django_setup_configuration.models import ConfigurationModel
from tests.conftest import assert_validation_errors_equal


class NestedConfigModel(ConfigurationModel):
    nested_foo: str
    nested_optional_bar: int | None = None


class ConfigModel(ConfigurationModel):
    foo: str
    nested_obj: NestedConfigModel


@pytest.fixture()
def valid_configuration_obj():
    return {
        "extra": "Extra vars at the root level are valid",
        "config_enabled": True,
        "the_namespace": {
            "foo": "a string",
            "nested_obj": {"nested_foo": "a nested string"},
        },
    }


@pytest.fixture()
def yaml_file_with_valid_configuration(yaml_file_factory, valid_configuration_obj):
    yaml_path = yaml_file_factory(valid_configuration_obj)
    return yaml_path


@pytest.fixture()
def yaml_file_with_invalid_configuration(yaml_file_factory):
    yaml_path = yaml_file_factory(
        {
            "config_enabled": 42,  # Should be bool
            "the_namespace": {
                "foo": "a string",
                "nested_obj": {
                    "nested_foo": False,
                    # No extra attributes allowed at config model level
                    "extra": "bar",
                },
            },
        }
    )
    return yaml_path


def test_init_from_valid_init_kwargs_does_not_raise(valid_configuration_obj):
    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        ConfigModel,
    )

    assert FlagModel(**valid_configuration_obj).model_dump() == {"config_enabled": True}
    assert SettingsModel(**valid_configuration_obj).model_dump() == {
        "the_namespace": {
            "foo": "a string",
            "nested_obj": {
                "nested_foo": "a nested string",
                "nested_optional_bar": None,
            },
        }
    }


def test_init_from_valid_yaml_does_not_raise(yaml_file_with_valid_configuration):
    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        ConfigModel,
        yaml_file=yaml_file_with_valid_configuration,
    )

    assert FlagModel().model_dump() == {"config_enabled": True}
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "a string",
            "nested_obj": {
                "nested_foo": "a nested string",
                "nested_optional_bar": None,
            },
        }
    }


def test_init_kwargs_override_yaml_file(yaml_file_with_valid_configuration):
    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        ConfigModel,
        yaml_file=yaml_file_with_valid_configuration,
    )

    assert FlagModel(config_enabled=False).model_dump() == {"config_enabled": False}
    assert SettingsModel(
        the_namespace={
            "foo": "a string",
            "nested_obj": {
                "nested_foo": "from init_kwargs",
            },
        }
    ).model_dump() == {
        "the_namespace": {
            "foo": "a string",
            "nested_obj": {
                "nested_foo": "from init_kwargs",
                "nested_optional_bar": None,
            },
        }
    }


def test_init_from_invalid_yaml_raises(
    yaml_file_with_invalid_configuration,
):
    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        ConfigModel,
        yaml_file=yaml_file_with_invalid_configuration,
    )

    with pytest.raises(ValidationError) as excinfo:
        FlagModel()

    assert_validation_errors_equal(
        excinfo,
        [
            {
                "type": "bool_parsing",
                "loc": ("config_enabled",),
                "msg": "Input should be a valid boolean, unable to interpret input",
                "input": 42,
            }
        ],
    )
    with pytest.raises(ValidationError) as excinfo:
        SettingsModel()

    assert_validation_errors_equal(
        excinfo,
        [
            {
                "type": "string_type",
                "loc": ("the_namespace", "nested_obj", "nested_foo"),
                "msg": "Input should be a valid string",
                "input": False,
            },
            {
                "type": "extra_forbidden",
                "loc": ("the_namespace", "nested_obj", "extra"),
                "msg": "Extra inputs are not permitted",
                "input": "bar",
            },
        ],
    )


def test_extra_args_at_config_model_level_raises(
    valid_configuration_obj,
):
    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        ConfigModel,
    )

    with_extra = {
        **valid_configuration_obj,
        "the_namespace": {**valid_configuration_obj["the_namespace"], "extra": 42},
    }

    with pytest.raises(ValidationError) as excinfo:
        assert SettingsModel(**with_extra)

    assert_validation_errors_equal(
        excinfo,
        [
            {
                "type": "extra_forbidden",
                "loc": ("the_namespace", "extra"),
                "msg": "Extra inputs are not permitted",
                "input": 42,
            }
        ],
    )
