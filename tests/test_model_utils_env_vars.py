from typing import Optional

import pydantic
import pytest

from django_setup_configuration.model_utils import create_config_source_models
from django_setup_configuration.models import ConfigurationModel
from testapp.models import SomeModel


class DeepNestedModel(ConfigurationModel):
    very_deep_field: str
    optional_deep_field: Optional[str] = pydantic.Field(default="deep_default")


class NestedModel(ConfigurationModel):
    nested_field: str
    optional_nested_field: Optional[str] = pydantic.Field(default="nested_default")
    deep_config: DeepNestedModel


class RootConfigModel(ConfigurationModel):
    """Root configuration model with Django model refs and nested structure"""

    # Field with Django model ref (foo field from SomeModel)
    foo: str

    # Required field without default
    required_field: str

    # Optional field with explicit default
    optional_field: Optional[str] = pydantic.Field(default="root_default")

    # Nested configuration
    nested_config: NestedModel

    # List of nested configurations
    nested_list: list[NestedModel]

    class Meta:
        django_model_refs = {SomeModel: ("foo",)}


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
                    "env": "FOO_VAR",
                }
            },
            "required_field": "some_required_value",
            "optional_field": "explicit_optional_value",
            "nested_config": {
                "nested_field": "nested_value",
                "optional_nested_field": "explicit_nested_value",
                "deep_config": {
                    "very_deep_field": "deep_value",
                    "optional_deep_field": "explicit_deep_value",
                },
            },
            "nested_list": [
                {
                    "nested_field": "list_nested_value",
                    "deep_config": {"very_deep_field": "list_deep_value"},
                }
            ],
        },
    }
)
def test_value_pointing_to_env_is_loaded_from_env(monkeypatch, yaml_file):
    monkeypatch.setenv("FOO_VAR", "foo_from_env")

    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        RootConfigModel,
        yaml_file=yaml_file,
    )

    assert FlagModel().model_dump() == {"config_enabled": True}
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "foo_from_env",  # Substituted from env
            "required_field": "some_required_value",
            "optional_field": "explicit_optional_value",
            "nested_config": {
                "nested_field": "nested_value",
                "optional_nested_field": "explicit_nested_value",
                "deep_config": {
                    "very_deep_field": "deep_value",
                    "optional_deep_field": "explicit_deep_value",
                },
            },
            "nested_list": [
                {
                    "nested_field": "list_nested_value",
                    "optional_nested_field": "nested_default",  # Uses default
                    "deep_config": {
                        "very_deep_field": "list_deep_value",
                        "optional_deep_field": "deep_default",  # Uses default
                    },
                }
            ],
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "MISSING_FOO_VAR",
                }
            },
            "required_field": "some_required_value",
            "nested_config": {
                "nested_field": "nested_value",
                "deep_config": {"very_deep_field": "deep_value"},
            },
            "nested_list": [],
        },
    }
)
def test_raise_on_nonexistent_environment_variable_without_default_or_fallthrough(
    yaml_file,
):
    # Note that we don't set/monkeypatch an environment variable

    with pytest.raises(ValueError) as error:
        _, SettingsModel = create_config_source_models(
            "config_enabled",
            "the_namespace",
            RootConfigModel,
            yaml_file=yaml_file,
        )
        SettingsModel().model_dump()

    assert str(error.value) == (
        "Required environment variable 'MISSING_FOO_VAR' not found for field 'foo'.\n"
        "Set the environment variable 'MISSING_FOO_VAR' or update your YAML "
        "configuration."
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
            "required_field": "some_required_value",
            "nested_config": {
                "nested_field": "nested_value",
                "deep_config": {"very_deep_field": "deep_value"},
            },
            "nested_list": [],
        },
    }
)
def test_exception_is_raised_on_incorrect_env_configuration(yaml_file):
    with pytest.raises(pydantic.ValidationError) as error:
        _, SettingsModel = create_config_source_models(
            "config_enabled",
            "the_namespace",
            RootConfigModel,
            yaml_file=yaml_file,
        )
        SettingsModel()

    errors = error.value.errors(
        include_url=False, include_context=False, include_input=False
    )
    assert len(errors) == 1
    assert errors[0]["type"] == "missing"
    assert errors[0]["loc"] == ("env",)


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "FOO_VAR",
                }
            },
            "required_field": "some_required_value",
            "nested_config": {
                "nested_field": "nested_value",
                "optional_nested_field": {
                    "value_from": {
                        "env": "NESTED_VAR",
                    }
                },
                "deep_config": {
                    "very_deep_field": "deep_value",
                    "optional_deep_field": {
                        "value_from": {
                            "env": "DEEP_VAR",
                        }
                    },
                },
            },
            "nested_list": [],
        },
    }
)
def test_value_pointing_to_env_is_loaded_from_nested_env(monkeypatch, yaml_file):
    monkeypatch.setenv("FOO_VAR", "foo_from_env")
    monkeypatch.setenv("NESTED_VAR", "nested_from_env")
    monkeypatch.setenv("DEEP_VAR", "deep_from_env")

    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        RootConfigModel,
        yaml_file=yaml_file,
    )

    assert FlagModel().model_dump() == {"config_enabled": True}
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "foo_from_env",
            "required_field": "some_required_value",
            "optional_field": "root_default",
            "nested_config": {
                "nested_field": "nested_value",
                "optional_nested_field": "nested_from_env",
                "deep_config": {
                    "very_deep_field": "deep_value",
                    "optional_deep_field": "deep_from_env",
                },
            },
            "nested_list": [],
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "FOO_VAR",
                }
            },
            "required_field": "some_required_value",
            "nested_config": {
                "nested_field": "nested_value",
                "deep_config": {"very_deep_field": "deep_value"},
            },
            "nested_list": [
                {
                    "nested_field": {
                        "value_from": {
                            "env": "LIST_NESTED_VAR",
                        }
                    },
                    "deep_config": {
                        "very_deep_field": "list_deep_value",
                        "optional_deep_field": {
                            "value_from": {
                                "env": "LIST_DEEP_VAR",
                            }
                        },
                    },
                },
                {
                    "nested_field": "static_nested_value",
                    "deep_config": {"very_deep_field": "static_deep_value"},
                },
            ],
        },
    }
)
def test_value_pointing_to_env_is_loaded_from_nested_env_list(monkeypatch, yaml_file):
    monkeypatch.setenv("FOO_VAR", "foo_from_env")
    monkeypatch.setenv("LIST_NESTED_VAR", "list_nested_from_env")
    monkeypatch.setenv("LIST_DEEP_VAR", "list_deep_from_env")

    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        RootConfigModel,
        yaml_file=yaml_file,
    )

    assert FlagModel().model_dump() == {"config_enabled": True}
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "foo_from_env",
            "required_field": "some_required_value",
            "optional_field": "root_default",
            "nested_config": {
                "nested_field": "nested_value",
                "optional_nested_field": "nested_default",
                "deep_config": {
                    "very_deep_field": "deep_value",
                    "optional_deep_field": "deep_default",
                },
            },
            "nested_list": [
                {
                    "nested_field": "list_nested_from_env",
                    "optional_nested_field": "nested_default",
                    "deep_config": {
                        "very_deep_field": "list_deep_value",
                        "optional_deep_field": "list_deep_from_env",
                    },
                },
                {
                    "nested_field": "static_nested_value",
                    "optional_nested_field": "nested_default",
                    "deep_config": {
                        "very_deep_field": "static_deep_value",
                        "optional_deep_field": "deep_default",
                    },
                },
            ],
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "nested_list": [
                {
                    "nested_field": {
                        "value_from": {
                            "env": "FIRST_NESTED_VAR",
                        }
                    },
                    "deep_config": {"very_deep_field": "first_deep_value"},
                },
                {
                    "nested_field": "second_nested_value",
                    "deep_config": {"very_deep_field": "second_deep_value"},
                },
            ]
        },
    }
)
def test_value_pointing_to_env_is_loaded_from_env_with_list(monkeypatch, yaml_file):
    monkeypatch.setenv("FIRST_NESTED_VAR", "first_from_env")

    class ListOnlyModel(ConfigurationModel):
        nested_list: list[NestedModel]

    FlagModel, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        ListOnlyModel,
        yaml_file=yaml_file,
    )

    assert FlagModel().model_dump() == {"config_enabled": True}
    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "nested_list": [
                {
                    "nested_field": "first_from_env",
                    "optional_nested_field": "nested_default",
                    "deep_config": {
                        "very_deep_field": "first_deep_value",
                        "optional_deep_field": "deep_default",
                    },
                },
                {
                    "nested_field": "second_nested_value",
                    "optional_nested_field": "nested_default",
                    "deep_config": {
                        "very_deep_field": "second_deep_value",
                        "optional_deep_field": "deep_default",
                    },
                },
            ]
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {"foo": {"value_from": "not a dict"}},
    }
)
def test_raise_when_value_from_is_not_dict(yaml_file):
    class SimpleOptionalModel(ConfigurationModel):
        foo: Optional[str] = pydantic.Field(default="default_foo")

    with pytest.raises(pydantic.ValidationError) as error:
        _, SettingsModel = create_config_source_models(
            "config_enabled",
            "the_namespace",
            SimpleOptionalModel,
            yaml_file=yaml_file,
        )
        SettingsModel()

    errors = error.value.errors(
        include_url=False, include_context=False, include_input=False
    )
    assert len(errors) == 1
    assert errors[0]["type"] == "model_type"
    assert errors[0]["loc"] == ()


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "MISSING_VAR",
                    "default": "fallback_value",
                }
            },
        },
    }
)
def test_default_value_is_used_when_env_var_not_found(yaml_file):
    class SimpleOptionalModel(ConfigurationModel):
        foo: Optional[str] = pydantic.Field(default="default_foo")

    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        SimpleOptionalModel,
        yaml_file=yaml_file,
    )

    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "fallback_value",  # Uses default from value_from
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "MISSING_VAR_WITH_NULL_DEFAULT",
                    "default": None,  # Explicit null default
                }
            },
        },
    }
)
def test_default_null_value_is_used_when_env_var_not_found(yaml_file):
    class SimpleOptionalModel(ConfigurationModel):
        foo: Optional[str] = pydantic.Field(default="default_foo")

    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        SimpleOptionalModel,
        yaml_file=yaml_file,
    )

    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": None,  # Uses explicit null default from value_from
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "field_with_null_default": {
                "value_from": {
                    "env": "MISSING_VAR_NULL",
                    "default": None,  # Explicit null default
                }
            },
            "field_with_no_default_but_optional": {
                "value_from": {
                    "env": "MISSING_VAR_OPTIONAL",
                    "required": False,  # No default, but not require: should be omitted
                }
            },
            "required_field": "some_required_value",
        },
    }
)
def test_null_default_differs_from_absent_default(yaml_file):
    class MixedModel(ConfigurationModel):
        field_with_null_default: Optional[str] = pydantic.Field(
            default="model_default_1"
        )
        field_with_no_default_but_optional: Optional[str] = pydantic.Field(
            default="model_default_2"
        )
        required_field: str

    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        MixedModel,
        yaml_file=yaml_file,
    )

    result = SettingsModel().model_dump()

    assert result == {
        "the_namespace": {
            "field_with_null_default": None,  # Uses explicit null from value_from
            "field_with_no_default_but_optional": "model_default_2",  # Model default
            "required_field": "some_required_value",
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "PRESENT_VAR",
                    "default": "fallback_value",
                }
            },
        },
    }
)
def test_env_var_takes_precedence_over_default(monkeypatch, yaml_file):
    class SimpleOptionalModel(ConfigurationModel):
        foo: Optional[str] = pydantic.Field(default="default_foo")

    monkeypatch.setenv("PRESENT_VAR", "env_value")

    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        SimpleOptionalModel,
        yaml_file=yaml_file,
    )

    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "env_value",  # Env var takes precedence
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "MISSING_VAR",
                    "required": False,
                }
            },
        },
    }
)
def test_required_false_falls_back_to_model_default_on_missing_env(yaml_file):
    class SimpleOptionalModel(ConfigurationModel):
        foo: Optional[str] = pydantic.Field(default="default_foo")

    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        SimpleOptionalModel,
        yaml_file=yaml_file,
    )

    result = SettingsModel().model_dump()

    assert result == {
        "the_namespace": {
            "foo": "default_foo",  # Uses Pydantic default after _OMIT_KEY
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "PRESENT_VAR",
                    "required": False,
                }
            },
        },
    }
)
def test_required_false_uses_env_var_when_available(monkeypatch, yaml_file):
    class SimpleOptionalModel(ConfigurationModel):
        foo: Optional[str] = pydantic.Field(default="default_foo")

    monkeypatch.setenv("PRESENT_VAR", "env_value")

    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        SimpleOptionalModel,
        yaml_file=yaml_file,
    )

    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "foo": "env_value",  # Uses env var when present
        }
    }


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "foo": {
                "value_from": {
                    "env": "SOME_VAR",
                    "required": False,
                    "default": "default_value",
                }
            },
        },
    }
)
def test_raise_when_required_and_default_both_specified(yaml_file):
    class SimpleOptionalModel(ConfigurationModel):
        foo: Optional[str] = pydantic.Field(default="default_foo")

    with pytest.raises(pydantic.ValidationError) as error:
        _, SettingsModel = create_config_source_models(
            "config_enabled",
            "the_namespace",
            SimpleOptionalModel,
            yaml_file=yaml_file,
        )
        SettingsModel()

    errors = error.value.errors(
        include_url=False, include_context=False, include_input=False
    )
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert (
        "'required' and 'default' cannot both be specified in 'value_from'"
        in errors[0]["msg"]
    )


@pytest.mark.yaml_configuration(
    {
        "config_enabled": True,
        "the_namespace": {
            "nested_list": [
                {
                    # First item: not required and env var not set - should omit key
                    "nested_field": {
                        "value_from": {
                            "env": "MISSING_VAR_1",
                            "required": False,
                        }
                    },
                    "deep_config": {"very_deep_field": "first_deep"},
                },
                {
                    # Second item: has env var available - should substitute
                    "nested_field": {
                        "value_from": {
                            "env": "AVAILABLE_VAR",
                        }
                    },
                    "deep_config": {"very_deep_field": "second_deep"},
                },
                {
                    # Third item: not required and env var not set - should omit key
                    "nested_field": {
                        "value_from": {
                            "env": "MISSING_VAR_2",
                            "required": False,
                        }
                    },
                    "deep_config": {"very_deep_field": "third_deep"},
                },
                {
                    # Fourth item: has default
                    "nested_field": {
                        "value_from": {
                            "env": "MISSING_VAR_3",
                            "default": "default_value",
                        }
                    },
                    "deep_config": {"very_deep_field": "fourth_deep"},
                },
            ],
        },
    }
)
def test_list_processes_all_elements_and_handles_omit_keys(monkeypatch, yaml_file):
    # Only set one env var, leave others missing
    monkeypatch.setenv("AVAILABLE_VAR", "env_substituted_value")

    class OptionalNestedModel(ConfigurationModel):
        nested_field: Optional[str] = pydantic.Field(default="nested_default")
        optional_nested_field: Optional[str] = pydantic.Field(default="nested_default")
        deep_config: DeepNestedModel

    class ListOnlyModel(ConfigurationModel):
        nested_list: list[OptionalNestedModel]

    _, SettingsModel = create_config_source_models(
        "config_enabled",
        "the_namespace",
        ListOnlyModel,
        yaml_file=yaml_file,
    )

    assert SettingsModel().model_dump() == {
        "the_namespace": {
            "nested_list": [
                {
                    "nested_field": "nested_default",  # Fall back to model default
                    "optional_nested_field": "nested_default",
                    "deep_config": {
                        "very_deep_field": "first_deep",
                        "optional_deep_field": "deep_default",
                    },
                },
                {
                    "nested_field": "env_substituted_value",  # Env var substitution
                    "optional_nested_field": "nested_default",
                    "deep_config": {
                        "very_deep_field": "second_deep",
                        "optional_deep_field": "deep_default",
                    },
                },
                {
                    "nested_field": "nested_default",  # Fall back to model default
                    "optional_nested_field": "nested_default",
                    "deep_config": {
                        "very_deep_field": "third_deep",
                        "optional_deep_field": "deep_default",
                    },
                },
                {
                    "nested_field": "default_value",  # Fall back to model default
                    "optional_nested_field": "nested_default",
                    "deep_config": {
                        "very_deep_field": "fourth_deep",
                        "optional_deep_field": "deep_default",
                    },
                },
            ],
        },
    }
