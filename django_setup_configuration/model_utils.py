import collections
import os
from pathlib import Path
from typing import Any, TypeAlias

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


JSONValue: TypeAlias = dict | list | str | bool | float | int | None


class YamlWithEnvSubstitution(YamlConfigSettingsSource):
    """Modified YAML source that recursively substitutes markers with env vars."""

    def __init__(self, namespace: str, **kwargs):
        self.namespace = namespace
        super().__init__(**kwargs)

    @staticmethod
    def substitute(field: JSONValue, field_name: str) -> JSONValue:
        match field:
            case dict():
                if "value_from" in field:
                    if "env" in field["value_from"]:
                        field_value = field["value_from"]["env"]
                        if field_value in os.environ:
                            return os.environ[field_value]
                        else:
                            raise ValueError(
                                f"Required environment variable '{field_value}' not "
                                f"found for field '{field_name}'.\nSet the environment "
                                f"variable '{field_value}' or update your YAML "
                                "configuration."
                            )
                    else:
                        raise ValueError(
                            f"Invalid YAML configuration for field '{field_name}'.\n"
                            "When using 'value_from', specify 'env' with the "
                            f"environment variable name:\n  {field_name}:\n    "
                            "value_from:\n      env: YOUR_ENV_VAR_NAME"
                        )
                else:
                    for inner_field_name in field.keys():
                        inner_field = field[inner_field_name]
                        field[inner_field_name] = YamlWithEnvSubstitution.substitute(
                            field=inner_field, field_name=inner_field_name
                        )
                    return field
            case list():
                objects = field
                for obj in objects:
                    YamlWithEnvSubstitution.substitute(field=obj, field_name=field_name)
                    return field
            case _:
                return field

    def _read_file(self, file_path: Path) -> dict[str, Any]:
        # We override this method to perform environment variable substitution before
        # the parent class validates the loaded data against the Pydantic model, which
        # happens in the constructor right after calling self._read_file
        yaml_data = super()._read_file(file_path)
        return self.substitute(yaml_data, self.namespace)


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
