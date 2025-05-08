from typing import Literal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_slug

import pytest
from pydantic import ValidationError
from pydantic.fields import PydanticUndefined

from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from testapp.models import DjangoModel, StrChoices


def test_meta_spec_is_equivalent_to_inline_fields():
    class ConfigMeta(ConfigurationModel):
        required_int = DjangoModelRef(DjangoModel, field_name="required_int")
        int_with_default = DjangoModelRef(DjangoModel, field_name="int_with_default")
        nullable_and_blank_str = DjangoModelRef(
            DjangoModel, field_name="nullable_and_blank_str"
        )
        field_with_help_text = DjangoModelRef(
            DjangoModel, field_name="field_with_help_text"
        )

    class ConfigInline(ConfigurationModel):
        class Meta:
            django_model_refs = {
                DjangoModel: [
                    "required_int",
                    "int_with_default",
                    "nullable_and_blank_str",
                    "field_with_help_text",
                ]
            }

    for field_meta, field_inline in zip(
        ConfigMeta.model_fields.values(), ConfigInline.model_fields.values()
    ):
        assert field_meta.field_name == field_inline.field_name
        assert field_meta.annotation == field_inline.annotation
        assert field_meta.default == field_inline.default
        assert field_meta.description == field_inline.description
        assert field_meta.is_required() == field_inline.is_required()


def test_annotation_overrides_django_type():
    class Config(ConfigurationModel):
        overriden_str: str = DjangoModelRef(DjangoModel, "required_int")

    field = Config.model_fields["overriden_str"]

    assert field.annotation == str
    assert field.default == PydanticUndefined
    assert field.is_required() is True


@pytest.mark.parametrize(
    "invalid_values",
    (
        "",
        "hello world",
        "user@email.com",
        "$price",
        "my.variable",
        "résumé",
        "hello!",
        "!",
        "#",
        "+",
    ),
)
def test_slug_validation_fails_on_both_pydantic_and_django(invalid_values):

    class Config(ConfigurationModel):
        slug = DjangoModelRef(DjangoModel, "slug")

    with pytest.raises(ValidationError):
        Config(slug=invalid_values)

    with pytest.raises(DjangoValidationError):
        validate_slug(invalid_values)


@pytest.mark.parametrize(
    "valid_values",
    (
        "a",
        "foo-bar",
        "foo_bar",
        "foo_bar_baz",
        "foo-bar-baz",
        "fO0-B4r-Baz",
        "foo-bar-baz",
        "foobarbaz",
        "FooBarBaz",
    ),
)
def test_slug_validation_succeeds_on_both_pydantic_and_django(valid_values):

    class Config(ConfigurationModel):
        slug = DjangoModelRef(DjangoModel, "slug")

    Config.model_validate(dict(slug=valid_values))
    validate_slug(valid_values)  # does not raise


def test_no_default_makes_field_required():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {DjangoModel: ["required_int"]}

    field = Config.model_fields["required_int"]

    assert field.annotation == int
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_default_is_taken_from_field():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {DjangoModel: ["int_with_default"]}

    field = Config.model_fields["int_with_default"]

    assert field.annotation == int
    assert field.default == 42
    assert field.is_required() is False


def test_explicit_default_overrides_model_field_default():

    class Config(ConfigurationModel):
        int_with_default = DjangoModelRef(DjangoModel, "int_with_default")
        int_with_overridden_default = DjangoModelRef(
            DjangoModel, "int_with_default", default=1874
        )

    int_with_default_field = Config.model_fields["int_with_default"]
    int_with_overridden_default_field = Config.model_fields[
        "int_with_overridden_default"
    ]

    assert int_with_default_field.default == 42
    assert int_with_overridden_default_field.default == 1874

    assert (
        int_with_default_field.annotation
        == int_with_overridden_default_field.annotation
        == int
    )
    assert (
        int_with_default_field.is_required()
        is int_with_overridden_default_field.is_required()
        is False
    )


def test_blank_fields_have_default_added_as_literal():

    class Config(ConfigurationModel):
        blank_bool_with_default = DjangoModelRef(DjangoModel, "blank_bool_with_default")
        nullable_blank_bool_with_default = DjangoModelRef(
            DjangoModel, "nullable_blank_bool_with_default"
        )

    blank_bool_with_default = Config.model_fields["blank_bool_with_default"]
    nullable_blank_bool_with_default = Config.model_fields[
        "nullable_blank_bool_with_default"
    ]

    assert blank_bool_with_default.annotation == bool
    assert nullable_blank_bool_with_default.annotation == bool | None

    assert (
        blank_bool_with_default.is_required()
        is nullable_blank_bool_with_default.is_required()
        is False
    )


def test_null_is_true_sets_default_to_none():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {DjangoModel: ["nullable_int"]}

    field = Config.model_fields["nullable_int"]

    assert field.title == "nullable int"
    assert field.description is None
    assert field.annotation == int | None
    assert field.default is None
    assert field.is_required() is False


def test_null_prefers_explicit_default():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {DjangoModel: ["nullable_int_with_default"]}

    field = Config.model_fields["nullable_int_with_default"]

    assert field.title == "nullable int with default"
    assert field.description is None
    assert field.annotation == int
    assert field.default == 42
    assert field.is_required() is False


def test_null_is_true_sets_default_to_none_for_str_fields():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {DjangoModel: ["nullable_and_blank_str"]}

    field = Config.model_fields["nullable_and_blank_str"]

    assert field.title == "nullable and blank str"
    assert field.description is None
    assert field.annotation == str | None
    assert field.default is None
    assert field.is_required() is False


def test_blank_is_true_null_is_false_sets_default_to_empty_str_for_str_fields():
    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {DjangoModel: ["blank_str"]}

    field = Config.model_fields["blank_str"]

    assert field.title == "blank str"
    assert field.description is None
    assert field.annotation == str
    assert field.default == ""
    assert field.is_required() is False


def test_help_text_sets_description():
    class Config(ConfigurationModel):
        field_with_help_text = DjangoModelRef(DjangoModel, "field_with_help_text")

    field = Config.model_fields["field_with_help_text"]

    assert field.title == "field with help text"
    assert field.description == "This is the help text"
    assert field.annotation == int
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_verbose_name_sets_title():
    class Config(ConfigurationModel):
        field_with_verbose_name = DjangoModelRef(DjangoModel, "field_with_verbose_name")

    field = Config.model_fields["field_with_verbose_name"]

    assert field.title == "The Verbose Name"
    assert field.description is None
    assert field.annotation == int
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_unmapped_type_raises():

    with pytest.raises(ValueError):

        class Config(ConfigurationModel):
            foreign_key = DjangoModelRef(DjangoModel, "foreign_key")


def test_unmapped_type_does_not_raise_if_annotation_is_overridden():

    class Config(ConfigurationModel):
        foreign_key: bool = DjangoModelRef(DjangoModel, "foreign_key")

    field = Config.model_fields["foreign_key"]

    assert field.title == "foreign key"
    assert field.description is None
    assert field.annotation == bool
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_str_with_choices_has_literal_annotation():

    class Config(ConfigurationModel):
        str_with_choices_and_default = DjangoModelRef(
            DjangoModel, "str_with_choices_and_default"
        )

    field = Config.model_fields["str_with_choices_and_default"]

    assert field.title == "str with choices and default"
    assert field.description is None
    assert field.annotation == Literal["foo", "bar"]
    assert field.default == StrChoices.bar
    assert field.is_required() is False


def test_int_with_choices_has_literal_annotation():

    class Config(ConfigurationModel):
        int_with_choices = DjangoModelRef(DjangoModel, "int_with_choices")

    field = Config.model_fields["int_with_choices"]

    assert field.title == "int with choices"
    assert field.description is None
    assert field.annotation == Literal[1, 8]
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_int_with_choices_callable_has_literal_annotation():

    class Config(ConfigurationModel):
        int_with_choices_callable = DjangoModelRef(
            DjangoModel, "int_with_choices_callable"
        )

    field = Config.model_fields["int_with_choices_callable"]

    assert field.title == "int with choices callable"
    assert field.description is None
    assert field.annotation == Literal[1, 8]
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_int_with_choices_and_override_has_overridden_annotation():

    class Config(ConfigurationModel):
        int_with_choices: bool = DjangoModelRef(DjangoModel, "int_with_choices")

    field = Config.model_fields["int_with_choices"]

    assert field.title == "int with choices"
    assert field.description is None
    assert field.annotation == bool
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_str_with_choices_and_blank_allows_empty_string_in_annotation():

    class Config(ConfigurationModel):
        str_with_choices_and_blank = DjangoModelRef(
            DjangoModel, "str_with_choices_and_blank"
        )

    field = Config.model_fields["str_with_choices_and_blank"]

    assert field.title == "str with choices and blank"
    assert field.description is None
    assert field.annotation == Literal["foo", "bar"] | Literal[""]
    assert field.default == ""
    assert field.is_required() is False


def test_int_with_choices_and_blank_adds_default_in_annotation():

    class Config(ConfigurationModel):
        int_with_choices_and_blank = DjangoModelRef(
            DjangoModel, "int_with_choices_and_blank"
        )

    field = Config.model_fields["int_with_choices_and_blank"]

    assert field.title == "int with choices and blank"
    assert field.description is None
    assert field.annotation == Literal[1, 8] | None
    assert field.default is None
    assert field.is_required() is False


def test_int_with_choices_and_blank_and_non_choice_default_adds_default_in_annotation():

    class Config(ConfigurationModel):
        int_with_choices_and_blank_and_non_choice_default = DjangoModelRef(
            DjangoModel, "int_with_choices_and_blank_and_non_choice_default"
        )

    field = Config.model_fields["int_with_choices_and_blank_and_non_choice_default"]

    assert field.title == "int with choices and blank and non choice default"
    assert field.description is None
    assert field.annotation == Literal[1, 8] | Literal[42]
    assert field.default == 42
    assert field.is_required() is False


def test_choices_with_incorrectly_typed_default_is_not_validated():

    class Config(ConfigurationModel):
        str_with_choices_and_incorrectly_typed_default = DjangoModelRef(
            DjangoModel, "str_with_choices_and_incorrectly_typed_default"
        )
        str_with_choices_and_incorrectly_typed_default_factory = DjangoModelRef(
            DjangoModel, "str_with_choices_and_incorrectly_typed_default_factory"
        )

    config = Config()
    assert config.str_with_choices_and_incorrectly_typed_default == 1974
    assert config.str_with_choices_and_incorrectly_typed_default_factory == 1985


def test_defaults_and_null_flags_are_respected_for_unmapped_fields():
    class Config(ConfigurationModel):
        unmapped_django_field_with_default_without_blank: str = DjangoModelRef(
            DjangoModel, "unmapped_django_field_with_default_without_blank"
        )
        unmapped_django_field_with_default_with_blank: str = DjangoModelRef(
            DjangoModel, "unmapped_django_field_with_default_with_blank"
        )
        unmapped_django_field_without_default_without_blank: str = DjangoModelRef(
            DjangoModel, "unmapped_django_field_without_default_without_blank"
        )
        unmapped_django_field_without_default_with_blank: str = DjangoModelRef(
            DjangoModel, "unmapped_django_field_without_default_with_blank"
        )

    assert (
        Config.model_fields["unmapped_django_field_with_default_without_blank"].default
        == Config.model_fields["unmapped_django_field_with_default_with_blank"].default
        == "foo"
    )
    assert (
        Config.model_fields[
            "unmapped_django_field_without_default_without_blank"
        ].default
        is PydanticUndefined
    )
    assert (
        Config.model_fields["unmapped_django_field_without_default_with_blank"].default
        == ""
    )
