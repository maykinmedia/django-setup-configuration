import collections

from pydantic import create_model
from pydantic.fields import Field
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    InitSettingsSource,
    SecretsSettingsSource,
    SettingsConfigDict,
)
from pydantic_settings.sources import (
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)

from django_setup_configuration.models import ConfigurationModel

ConfigSourceModels = collections.namedtuple(
    "ConfigSourceModels", ["enable_setting_source", "config_settings_source"]
)


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
            # The convention is that a step's settings are located under a key
            # that matches the step's `namespace`, thus we don't need an
            # additional prefix in the env vars, as these will already be
            # prefixed with `namespace__`.
            env_prefix="",
            # Follow the well-known (Django) convention here
            env_nested_delimiter="__",
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
                YamlConfigSettingsSource(
                    settings_cls,
                    yaml_file=yaml_file,
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
