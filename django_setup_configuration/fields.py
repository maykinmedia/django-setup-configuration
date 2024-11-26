import datetime
import decimal
from typing import Any, Literal, Mapping

from django.apps import apps as django_apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.fields import NOT_PROVIDED, Field

from pydantic.fields import FieldInfo


def get_model_from_ref(ref: str | type[models.Model]) -> type[models.Model]:
    """
    Retrieves a Django model class from the provided reference.

    Args:
        ref (str | type[django.db.models.Model]): Either a Django model class
            or a string in the format "app_label.model".

    Returns:
        The Django model class.

    Raises:
        ValueError: If the input is not a valid Django model or a string in
        the format "app_label.model".
    """
    if isinstance(ref, str):
        parts = ref.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Cannot import model from {ref}: use `app_label.model_name`"
            )
        app_label, model_name = parts
        return django_apps.get_model(app_label, model_name)

    if issubclass(ref, models.Model):
        return ref

    raise ValueError(
        f"Invalid model input: {ref}. Expected a Django model class or a "
        "string in the format 'app_label.model'."
    )


class UNMAPPED_DJANGO_FIELD:
    pass


class DjangoModelRefInfo(FieldInfo):
    """
    A FieldInfo representing a reference to a field on a Django model.

    Do not use this class directly, but use `DjangoModelRef` instead.
    """

    def __init__(
        self,
        model: type[models.Model] | str,
        field_name: str,
        *,
        default: Any = NOT_PROVIDED,
        **kwargs,
    ):

        try:
            resolved_model = get_model_from_ref(model)
            self.django_field = resolved_model._meta.get_field(field_name)
        except FieldDoesNotExist:
            raise ValueError(
                f"Field '{field_name}' does not exist in model "
                f"{model if isinstance(model, str) else model.__class__}"
            )

        self.model = model
        self.field_name = field_name
        self.python_type = self._get_python_type(self.django_field)
        field_info_creation_kwargs: dict[str, Any] = {
            "title": self.django_field.verbose_name,
        }
        if description := (kwargs.pop("description", self.django_field.help_text)):
            field_info_creation_kwargs["description"] = description

        inferred_default = NOT_PROVIDED
        if default is not NOT_PROVIDED:
            # Override the field default with the provided value...
            inferred_default = default
        else:
            if (django_default := self.django_field.default) is not NOT_PROVIDED:
                # ...otherwise, use the Django field's default (callable or value)
                if callable(django_default):
                    field_info_creation_kwargs["default_factory"] = django_default
                else:
                    inferred_default = django_default
            else:
                # If nullable, mark the field is optional with a default of None
                if self.django_field.null:
                    inferred_default = None
                    self.python_type = self.python_type | None

                # For strings that can have blank=True and null=False (the
                # recommended approach), set an empty string as the default
                if (
                    self.django_field.blank
                    and not self.django_field.null
                    and self.python_type == str
                ):
                    inferred_default = ""
                    self.python_type = self.python_type | None

        field_info_creation_kwargs["annotation"] = self.python_type
        if inferred_default is not NOT_PROVIDED:
            field_info_creation_kwargs["default"] = inferred_default

        return super().__init__(**field_info_creation_kwargs)

    @staticmethod
    def _get_python_type(
        django_field: Field,
    ):
        """Map Django field types to Python types."""
        if choices := getattr(django_field, "choices"):
            choice_values = tuple(choice[0] for choice in choices)
            return Literal[choice_values]

        mapping: Mapping[
            type[Field],
            type[
                str
                | int
                | float
                | bool
                | decimal.Decimal
                | datetime.time
                | datetime.datetime
                | datetime.timedelta
                | dict
            ],
        ] = {
            # String-based fields
            models.CharField: str,
            models.TextField: str,
            models.EmailField: str,
            models.URLField: str,
            models.SlugField: str,
            models.UUIDField: str,
            # Integer-based fields
            models.AutoField: int,
            models.SmallAutoField: int,
            models.IntegerField: int,
            models.BigIntegerField: int,
            models.PositiveIntegerField: int,
            models.PositiveSmallIntegerField: int,
            models.PositiveBigIntegerField: int,
            models.SmallIntegerField: int,
            # Other numeric
            models.FloatField: float,
            models.DecimalField: decimal.Decimal,
            # Datetime
            models.TimeField: datetime.time,
            models.DateTimeField: datetime.datetime,
            models.DurationField: datetime.timedelta,
            # Misc
            models.BooleanField: bool,
            models.JSONField: dict,
        }
        try:
            field_type = type(django_field)
            return mapping[field_type]
        except KeyError:
            # If a type is unmapped, we return a sentinel value here to be picked up
            # by the metaclass, which will subsequently check if the user has
            # overridden the type annotation. If not, an exception will be raised
            # prompting the user to do so.
            return UNMAPPED_DJANGO_FIELD


def DjangoModelRef(
    model: type[models.Model] | str,
    field_name: str,
    *,
    default: Any = NOT_PROVIDED,
    **kwargs,
) -> Any:
    """
    A custom Pydantic field that takes its type and documentation from a Django model
    field.

    Note that in order to use this field, you must use `ConfigModel` as the base
    for your Pydantic model rather than the default BaseModel.

    Args:
        model (type[models.Model] | str): The Django model containing the reference
            field.
        field_name (str): The name of the references field.
        default (Any, optional): A default for this field, which will override
            any default set on the Django field.

    Example:
        from django.contrib.auth.models import User

        class UserConfigModel(ConfigModel):
            username = DjangoModelRef(User, "username")

    """
    return DjangoModelRefInfo(
        model=model,
        field_name=field_name,
        default=default,
        **kwargs,
    )
