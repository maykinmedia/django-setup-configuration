from typing import Any

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from django_setup_configuration.fields import (
    UNMAPPED_DJANGO_FIELD,
    DjangoModelRef,
    DjangoModelRefInfo,
    get_model_from_ref,
)


class DjangoRefsMetaclass(BaseModel.__class__):  # type: ignore
    """
    A custom Pydantic metaclass to derive annotations from `DjangoModelRef` fields.

    This metaclass is required to define DjangoModelRef without explicit
    annotations, instead taking the type from the underlying Django model field.
    Do not use this directly: instead, using `ConfigurationModel`.
    """

    def __new__(
        cls,
        name: str,
        bases: tuple[type[Any], ...],
        namespace: dict[str, Any],
        *args,
        **kwargs: Any,
    ):
        annotations = namespace.setdefault("__annotations__", {})

        if meta := namespace.get("Meta", None):
            if django_model_refs := getattr(meta, "django_model_refs", None):
                if not isinstance(django_model_refs, dict):
                    raise ValueError("`django_model_refs` must be a dict")

                for model_cls, fields in django_model_refs.items():
                    for field in fields:
                        namespace[field] = DjangoModelRef(
                            get_model_from_ref(model_cls), field
                        )

        for key, value in namespace.items():
            if isinstance(value, DjangoModelRefInfo):
                if key not in annotations:
                    # We were unable to map this type, and the user did not override
                    # the annotation. Raise an exception and prompt to user to add one.
                    if value.python_type is UNMAPPED_DJANGO_FIELD:
                        raise ValueError(
                            f"We could not infer a type for attribute `{key}` with "
                            f"Django field type {type(value.django_field)}. Please "
                            "add an explicit type annotation."
                        )

                    annotations[key] = value.python_type

        return super().__new__(cls, name, bases, namespace, *args, **kwargs)


class ConfigurationModel(BaseSettings, metaclass=DjangoRefsMetaclass):
    """
    A base for defining configuration settings to be used in a BaseConfigurationStep.
    """

    model_config = SettingsConfigDict(extra="forbid")
