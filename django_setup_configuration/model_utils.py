import collections
import os
from pathlib import Path
from typing import Any, Mapping, Sequence, TypeAlias

import pydantic
from pydantic import create_model
from pydantic.fields import Field
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    InitSettingsSource,
    SecretsSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from pydantic_settings.sources import PydanticBaseSettingsSource

from django_setup_configuration.models import ConfigurationModel

ConfigSourceModels = collections.namedtuple(
    "ConfigSourceModels", ["enable_setting_source", "config_settings_source"]
)


JSONValue: TypeAlias = (
    None | bool | int | float | str | Sequence["JSONValue"] | Mapping[str, "JSONValue"]
)


class _OmitKeyType:
    pass


_OMIT_KEY = _OmitKeyType()
"""Sentinel value to indicate that a key should be omitted from the result."""


_NO_DEFAULT = object()
"""Sentinel value to indicate no default was provided."""


class ValueFrom(pydantic.BaseModel):
    env: str
    required: bool = pydantic.Field(default=True)
    default: Any = pydantic.Field(default=_NO_DEFAULT)

    @pydantic.model_validator(mode="before")
    @classmethod
    def validate_required_and_default(cls, data):
        # Check for conflicting options - both required explicitly set and default
        # specified
        if isinstance(data, dict):
            has_explicit_required = "required" in data
            has_default = "default" in data

            if has_explicit_required and has_default:
                raise ValueError(
                    "'required' and 'default' cannot both be specified in 'value_from'."
                )
        return data


class YamlWithEnvSubstitution(YamlConfigSettingsSource):
    """Modified YAML source that recursively substitutes markers with env vars."""

    def __init__(self, namespace: str, **kwargs):
        self.namespace = namespace
        super().__init__(**kwargs)

    @staticmethod
    def substitute(field: JSONValue, field_name: str) -> JSONValue | _OmitKeyType:
        """Recursively substitute value_from patterns with environment variables."""
        substitute = YamlWithEnvSubstitution.substitute
        match field:
            case {"value_from": v} if value_from := ValueFrom.model_validate(v):
                match value_from:
                    case ValueFrom(env=name) if value := os.getenv(name):
                        return value
                    case ValueFrom(default=value) if value is not _NO_DEFAULT:
                        return value
                    case ValueFrom(required=False):
                        # No env var, no default, and not required. Return _OMIT_KEY so
                        # this key can be filtered out of the final object, to
                        # facilitate fallback to the model default.
                        return _OMIT_KEY
                    case ValueFrom(env=env_var_name):
                        # Environment variable missing, no default, and required - error
                        raise ValueError(
                            f"Required environment variable '{env_var_name}' not "
                            f"found for field '{field_name}'.\nSet the environment "
                            f"variable '{env_var_name}' or update your YAML "
                            "configuration."
                        )
            case {**fields}:
                return {k: substitute(field=v, field_name=k) for k, v in fields.items()}
            case [*items]:
                return [
                    sub
                    for i, item in enumerate(items)
                    if (sub := substitute(field=item, field_name=f"{field_name}[{i}]"))
                    is not _OMIT_KEY
                ]
            case _:
                return field

    @staticmethod
    def _drop_omitted_fields(data: JSONValue | _OmitKeyType) -> JSONValue:
        """Recursively remove all _OMIT_KEY values from the config data."""
        match data:
            case dict():
                return {
                    key: YamlWithEnvSubstitution._drop_omitted_fields(value)
                    for key, value in data.items()
                    if value is not _OMIT_KEY
                }
            case list():
                return [
                    YamlWithEnvSubstitution._drop_omitted_fields(item)
                    for item in data
                    if item is not _OMIT_KEY
                ]
            case _:
                return data

    def _read_file(self, file_path: Path) -> dict[str, Any]:
        # We override this method to perform environment variable substitution before
        # the parent class validates the loaded data against the Pydantic model, which
        # happens in the constructor right after calling self._read_file
        yaml_data = super()._read_file(file_path)

        # First pass: substitute all value_from patterns
        substituted_data = self.substitute(yaml_data, self.namespace)

        # Second pass: remove all _OMIT_KEY markers
        return self._drop_omitted_fields(substituted_data)


def create_config_source_models(
    enable_setting_key: str,
    namespace: str,
    config_model: ConfigurationModel,
    *,
    yaml_file: str | None = None,
) -> ConfigSourceModels:
    """
    Construct a pair of ConfigurationModels to load step settings from a source.

    Args:
        enable_setting_key (str): The key indicating the enabled/disabled flag.
        namespace (str): The key under which the actual config values will be stored.
        config_model (ConfigurationModel): The configuration model which will be loaded
            into `namespace` in the resulting config settings source model.
        yaml_file (str | None, optional): A YAML file from which to load the enable
            setting and config values. Defaults to None.

    Returns:
        ConfigSourceModels: A named tuple containing two ConfigurationModel classes,
            `enable_settings_source` to load the enabled flag from the yaml source,
            `config_settings_source` to load the configuration values from the yaml
            source.
    """

    class ConfigSourceBase(BaseSettings):
        """A Pydantic model that pulls its data from an external source."""

        model_config = SettingsConfigDict(
            # We assume our sources can have info for multiple steps combined
            extra="ignore",
        )

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: InitSettingsSource,
            env_settings: EnvSettingsSource,
            dotenv_settings: DotEnvSettingsSource,
            file_secret_settings: SecretsSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            # Note: lower indices have higher priority
            return (
                InitSettingsSource(settings_cls, init_kwargs=init_settings.init_kwargs),
            ) + (
                YamlWithEnvSubstitution(
                    namespace=namespace, settings_cls=settings_cls, yaml_file=yaml_file
                ),
            )

    # We build two models: one very simple model which simply contains a key for
    # the configured is-enabled flag, so that we can pull the flag from the
    # environment separately from all the other config files (which might not be
    # set). A second model contains only the actual attributes specified by the
    # ConfigurationModel in the step.

    # EnabledFlagSource => has only a single key, that matches the step's
    # `enable_setting` attribute.
    class EnabledFlagSource(ConfigSourceBase):
        pass

    flag_model_fields = {}
    flag_model_fields[enable_setting_key] = (
        bool,
        Field(
            default=False,
            description=f"Flag controls whether to enable the {namespace} config",
        ),
    )

    # ModelConfigBase contains a single key, equal to the `namespace` attribute,
    # which points to the actual model defined in the step, so with namespace
    # `auth` and a configuration model with a `username` and `password` string
    # we would get the equivalent of:
    #
    # class ConfigModel(BaseModel):
    #   username: str
    #   password: str
    #
    # class ModelConfigBase:
    #   auth: ConfigModel

    class ModelConfigBase(ConfigSourceBase):
        pass

    config_model_fields = {}
    config_model_fields[namespace] = (config_model, ...)

    ConfigSettingsSource = create_model(
        f"ConfigSettingsSource{namespace.capitalize()}",
        __base__=ModelConfigBase,
        **config_model_fields,
    )

    ConfigSettingsEnabledFlagSource = create_model(
        f"FlagConfigSource{namespace.capitalize()}",
        __base__=EnabledFlagSource,
        **flag_model_fields,
    )

    return ConfigSourceModels(ConfigSettingsEnabledFlagSource, ConfigSettingsSource)
