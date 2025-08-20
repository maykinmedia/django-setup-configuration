from typing import Optional

import pydantic
import pytest

from django_setup_configuration.model_utils import create_config_source_models
from django_setup_configuration.models import ConfigurationModel
from testapp.models import SomeModel


class MyConfigModel(ConfigurationModel):
    nested_obj: Optional[dict] = pydantic.Field()

    class Meta:
        django_model_refs = {SomeModel: ("foo",)}


class MyListedConfigModel(ConfigurationModel):
    items: list[MyConfigModel]


@pytest.fixture()
def yaml_file(request, yaml_file_factory):
    marker = request.node.get_closest_marker("yaml_configuration")
    yaml_data = marker.args[0]
    return yaml_file_factory(yaml_data)


@pytest.mark.yaml_configuration(
    {
        "extra": "Extra vars at the root level are valid",
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "FOO",
                }
            },
            "nested_obj": {"nested_foo": "a nested string"},
        },
    }
)
def test_value_pointing_to_env_is_loaded_from_env(monkeypatch, yaml_file):
    monkeypatch.setenv("FOO", "secret_from_env")

    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        MyConfigModel,
        yaml_file=yaml_file,
    )

    assert FlagModel().model_dump() == {"config_enabled": True}
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "secret_from_env",
            "nested_obj": {"nested_foo": "a nested string"},
        }
    }


@pytest.mark.yaml_configuration(
    {
        "extra": "Extra vars at the root level are valid",
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "FOO",
                }
            },
            "nested_obj": {"nested_foo": "a nested string"},
        },
    }
)
def test_exception_is_raised_on_nonexistent_environment_variable(yaml_file):
    # Note that we don't set/monkeypatch an environment variable

    with pytest.raises(ValueError) as error:
        _, SettingsModel = create_config_source_models(
            "config_enabled",
            "the_namespace",
            MyConfigModel,
            yaml_file=yaml_file,
        )
        SettingsModel().model_dump()

    assert str(error.value) == (
        "Required environment variable 'FOO' not found for field 'foo'.\nSet the "
        "environment variable 'FOO' or update your YAML configuration."
    )


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "bar": "foobar",
                }
            },
            "nested_obj": {"nested_foo": "a nested string"},
        },
    }
)
def test_exception_is_raised_on_incorrect_env_configuration(yaml_file):
    with pytest.raises(ValueError) as error:
        _, SettingsModel = create_config_source_models(
            "config_enabled",
            "the_namespace",
            MyConfigModel,
            yaml_file=yaml_file,
        )
        SettingsModel()

    assert str(error.value) == (
        "Invalid YAML configuration for field 'foo'.\nWhen using 'value_from', specify"
        " 'env' with the environment variable name:\n  foo:\n    value_from:\n      "
        "env: YOUR_ENV_VAR_NAME"
    )


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "FOO",
                }
            },
            "nested_obj": {
                "nested_foo": {
                    "very_nested_foo": {
                        "value_from": {
                            "env": "FOO",
                        }
                    }
                }
            },
        },
    }
)
def test_value_pointing_to_env_is_loaded_from_nested_env(monkeypatch, yaml_file):
    monkeypatch.setenv("FOO", "secret_from_env")

    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        MyConfigModel,
        yaml_file=yaml_file,
    )

    assert FlagModel().model_dump() == {"config_enabled": True}
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "secret_from_env",
            "nested_obj": {"nested_foo": {"very_nested_foo": "secret_from_env"}},
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "FOO",
                }
            },
            "nested_obj": {
                "nested_foo": [
                    {
                        "very_nested_foo": {
                            "value_from": {
                                "env": "FOO",
                            }
                        }
                    },
                    {"very_nested_foo": "hardcoded value"},
                ]
            },
        },
    }
)
def test_value_pointing_to_env_is_loaded_from_nested_env_list(
    monkeypatch,
    yaml_file,
):
    monkeypatch.setenv("FOO", "secret_from_env")

    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        MyConfigModel,
        yaml_file=yaml_file,
    )

    assert FlagModel().model_dump() == {"config_enabled": True}
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "secret_from_env",
            "nested_obj": {
                "nested_foo": [
                    {"very_nested_foo": "secret_from_env"},
                    {"very_nested_foo": "hardcoded value"},
                ]
            },
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "items": [
                {
                    "foo": {
                        "value_from": {
                            "env": "FOO",
                        },
                    },
                    "nested_obj": {"nested_foo": "a nested string"},
                },
                {
                    "foo": "some hardcoded secret",
                    "nested_obj": {"nested_foo": "a nested string"},
                },
            ],
        },
    }
)
def test_value_pointing_to_env_is_loaded_from_env_with_list(monkeypatch, yaml_file):
    monkeypatch.setenv("FOO", "secret_from_env")

    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        MyListedConfigModel,
        yaml_file=yaml_file,
    )

    assert FlagModel().model_dump() == {"config_enabled": True}
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "items": [
                {
                    "foo": "secret_from_env",
                    "nested_obj": {"nested_foo": "a nested string"},
                },
                {
                    "foo": "some hardcoded secret",
                    "nested_obj": {"nested_foo": "a nested string"},
                },
            ],
        },
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": "not_a_dict",
            },
            "nested_obj": {"nested_foo": "a nested string"},
        },
    }
)
def test_exception_is_raised_when_value_from_is_not_dict(yaml_file):
    with pytest.raises(ValueError) as error:
        _, SettingsModel = create_config_source_models(
            "config_enabled",
            "the_namespace",
            MyConfigModel,
            yaml_file=yaml_file,
        )
        SettingsModel()

    assert str(error.value) == (
        "Invalid YAML configuration for field 'foo'.\n'value_from' must be an object."
    )


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "NONEXISTENT_VAR",
                    "default": "default_value",
                }
            },
            "nested_obj": {"nested_foo": "a nested string"},
        },
    }
)
def test_default_value_is_used_when_env_var_not_found(yaml_file):
    # Note: We don't set NONEXISTENT_VAR environment variable
    
    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        MyConfigModel,
        yaml_file=yaml_file,
    )
    
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "default_value",
            "nested_obj": {"nested_foo": "a nested string"},
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "FOO",
                    "default": "default_value",
                }
            },
            "nested_obj": {"nested_foo": "a nested string"},
        },
    }
)
def test_env_var_takes_precedence_over_default(monkeypatch, yaml_file):
    monkeypatch.setenv("FOO", "env_value")
    
    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        MyConfigModel,
        yaml_file=yaml_file,
    )
    
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "env_value",
            "nested_obj": {"nested_foo": "a nested string"},
        }
    }
