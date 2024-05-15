from dataclasses import dataclass
from typing import Iterator, Mapping, Sequence, Type

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import OneToOneField
from django.utils.module_loading import import_string

from .constants import basic_field_descriptions
from .exceptions import ImproperlyConfigured


@dataclass(frozen=True, slots=True)
class ConfigField:
    name: str
    verbose_name: str
    description: str
    default_value: str
    field_description: str


class ConfigSettingsModel:
    models: list[Type[models.Model]]
    display_name: str
    namespace: str
    excluded_fields = ["id"]

    def __init__(self, *args, **kwargs):
        self.config_fields: list = []

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.update_field_descriptions()

        if not self.models:
            return

        for model in self.models:
            self.create_config_fields(
                exclude=self.excluded_fields,
                model=model,
            )

    def get_setting_name(self, field: ConfigField) -> str:
        return f"{self.namespace}_" + field.name.upper()

    @staticmethod
    def get_default_value(field: models.Field) -> str:
        default = field.default

        if default is NOT_PROVIDED:
            return "No default"

        # needed to make `generate_config_docs` idempotent
        # because UUID's are randomly generated
        if isinstance(field, models.UUIDField):
            return "random UUID string"

        # if default is a function, call the function to retrieve the value;
        # we don't immediately return because we need to check the type first
        # and cast to another type if necessary (e.g. list is unhashable)
        if callable(default):
            default = default()

        if isinstance(default, Mapping):
            return str(default)

        # check for field type as well to avoid splitting values from CharField
        if isinstance(field, (JSONField, ArrayField)) and isinstance(default, Sequence):
            try:
                return ", ".join(str(item) for item in default)
            except TypeError:
                return str(default)

        return default

    @staticmethod
    def update_field_descriptions() -> None:
        """
        Add custom fields + descriptions defined in settings to
        `basic_field_descriptions`
        """
        custom_fields = getattr(settings, "DJANGO_SETUP_CONFIG_CUSTOM_FIELDS", None)
        if not custom_fields:
            return

        for mapping in custom_fields:
            try:
                field = import_string(mapping["field"])
            except ImportError as exc:
                raise ImproperlyConfigured(
                    "\n\nSomething went wrong when importing {field}.\n"
                    "Check your settings for django-setup-configuration".format(
                        field=mapping["field"]
                    )
                ) from exc
            else:
                description = mapping["description"]
                basic_field_descriptions[field] = description

    @staticmethod
    def get_field_description(field: models.Field) -> str:
        # fields with choices
        if choices := field.choices:
            example_values = [choice[0] for choice in choices]
            return ", ".join(example_values)

        # other fields
        field_type = type(field)
        if field_type in basic_field_descriptions.keys():
            return basic_field_descriptions.get(field_type)
        return "No information available"

    def get_concrete_model_fields(self, model) -> Iterator[models.Field]:
        """
        Get all concrete fields for a given `model`, skipping over backreferences like
        `OneToOneRel` and fields that are blacklisted
        """
        return (
            field
            for field in model._meta.concrete_fields
            if field.name not in self.excluded_fields
        )

    def create_config_fields(
        self,
        exclude: list[str],
        model: Type[models.Model],
        relating_field: models.Field | None = None,
    ) -> None:
        """
        Create a `ConfigField` instance for each field of the given `model` and
        add it to `self.fields`

        Basic fields (`CharField`, `IntegerField` etc) constitute the base case,
        one-to-one relations (`OneToOneField`) are handled recursively

        `ForeignKey` and `ManyToManyField` are currently not supported (these require
        special care to avoid recursion errors)
        """

        model_fields = self.get_concrete_model_fields(model)

        for model_field in model_fields:
            if isinstance(model_field, OneToOneField):
                self.create_config_fields(
                    exclude=exclude,
                    model=model_field.related_model,
                    relating_field=model_field,
                )
            else:
                if model_field.name in self.excluded_fields:
                    continue

                # model field name could be "api_root",
                # but we need "xyz_service_api_root" (or similar) for consistency
                if relating_field:
                    name = f"{relating_field.name}_{model_field.name}"
                else:
                    name = model_field.name

                config_field = ConfigField(
                    name=name,
                    verbose_name=model_field.verbose_name,
                    description=model_field.help_text,
                    default_value=self.get_default_value(model_field),
                    field_description=self.get_field_description(model_field),
                )

                self.config_fields.append(config_field)

    def get_required_settings(self) -> list[str]:
        return [self.get_setting_name(field) for field in self.config_fields.required]
