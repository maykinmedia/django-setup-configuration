from django.conf import settings
from django.utils.module_loading import import_string

from .base import ConfigSettingsModel
from .exceptions import ImproperlyConfigured


class ConfigurationRegistry:
    def __init__(self):
        if not getattr(settings, "DJANGO_SETUP_CONFIG_REGISTER", None):
            raise ImproperlyConfigured("DJANGO_SETUP_CONFIG_REGISTER is not defined")

        if not all(
            (entry.get("model") for entry in settings.DJANGO_SETUP_CONFIG_REGISTER)
        ):
            raise ImproperlyConfigured(
                "Each entry for the DJANGO_SETUP_CONFIG_REGISTER setting "
                "must specify a configuration model"
            )

        self.register_config_models()

    def register_config_models(self) -> None:
        """
        Load config models specified in settings and set them as attributes on
        the instance
        """
        for mapping in settings.DJANGO_SETUP_CONFIG_REGISTER:
            file_name = mapping.get("file_name") or mapping["model"].split(".")[-1]

            try:
                model = import_string(mapping["model"])
            except ImportError as exc:
                exc.add_note(
                    "\nHint: check your settings for django-setup-configuration"
                )
                raise
            else:
                setattr(self, file_name, model)

    @property
    def fields(self) -> tuple[ConfigSettingsModel, ...]:
        return tuple(getattr(self, key) for key in vars(self).keys())

    @property
    def field_names(self) -> tuple[str, ...]:
        return tuple(key for key in vars(self).keys())
