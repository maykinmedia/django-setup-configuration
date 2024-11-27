from typing import Literal

import pytest
from pydantic.fields import PydanticUndefined

from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from testapp.models import StrChoices, TestModel


def test_meta_spec_is_equivalent_to_inline_fields():
    class ConfigMeta(ConfigurationModel):
        required_int = DjangoModelRef(TestModel, field_name="required_int")
        int_with_default = DjangoModelRef(TestModel, field_name="int_with_default")
        nullable_and_blank_str = DjangoModelRef(
            TestModel, field_name="nullable_and_blank_str"
        )
        field_with_help_text = DjangoModelRef(
            TestModel, field_name="field_with_help_text"
        )

    class ConfigInline(ConfigurationModel):
        class Meta:
            django_model_refs = {
                TestModel: [
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
        overriden_str: str = DjangoModelRef(TestModel, "required_int")

    field = Config.model_fields["overriden_str"]

    assert field.annotation == str
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_no_default_makes_field_required():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {TestModel: ["required_int"]}

    field = Config.model_fields["required_int"]

    assert field.annotation == int
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_default_is_taken_from_field():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {TestModel: ["int_with_default"]}

    field = Config.model_fields["int_with_default"]

    assert field.annotation == int
    assert field.default == 42
    assert field.is_required() is False


def test_explicit_default_overrides_model_field_default():

    class Config(ConfigurationModel):
        int_with_default = DjangoModelRef(TestModel, "int_with_default")
        int_with_overridden_default = DjangoModelRef(
            TestModel, "int_with_default", default=1874
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


def test_null_is_true_sets_default_to_none():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {TestModel: ["nullable_int"]}

    field = Config.model_fields["nullable_int"]

    assert field.title == "nullable int"
    assert field.description is None
    assert field.annotation == int | None
    assert field.default is None
    assert field.is_required() is False


def test_null_prefers_explicit_default():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {TestModel: ["nullable_int_with_default"]}

    field = Config.model_fields["nullable_int_with_default"]

    assert field.title == "nullable int with default"
    assert field.description is None
    assert field.annotation == int
    assert field.default == 42
    assert field.is_required() is False


def test_null_is_true_sets_default_to_none_for_str_fields():

    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {TestModel: ["nullable_and_blank_str"]}

    field = Config.model_fields["nullable_and_blank_str"]

    assert field.title == "nullable and blank str"
    assert field.description is None
    assert field.annotation == str | None
    assert field.default is None
    assert field.is_required() is False


def test_blank_is_true_null_is_false_sets_default_to_empty_str_for_str_fields():
    class Config(ConfigurationModel):
        class Meta:
            django_model_refs = {TestModel: ["blank_str"]}

    field = Config.model_fields["blank_str"]

    assert field.title == "blank str"
    assert field.description is None
    assert field.annotation == str | None
    assert field.default == ""
    assert field.is_required() is False


def test_help_text_sets_description():
    class Config(ConfigurationModel):
        field_with_help_text = DjangoModelRef(TestModel, "field_with_help_text")

    field = Config.model_fields["field_with_help_text"]

    assert field.title == "field with help text"
    assert field.description == "This is the help text"
    assert field.annotation == int
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_verbose_name_sets_title():
    class Config(ConfigurationModel):
        field_with_verbose_name = DjangoModelRef(TestModel, "field_with_verbose_name")

    field = Config.model_fields["field_with_verbose_name"]

    assert field.title == "The Verbose Name"
    assert field.description is None
    assert field.annotation == int
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_unmapped_type_raises():

    with pytest.raises(ValueError):

        class Config(ConfigurationModel):
            foreign_key = DjangoModelRef(TestModel, "foreign_key")


def test_unmapped_type_does_not_raise_if_annotation_is_overridden():

    class Config(ConfigurationModel):
        foreign_key: bool = DjangoModelRef(TestModel, "foreign_key")

    field = Config.model_fields["foreign_key"]

    assert field.title == "foreign key"
    assert field.description is None
    assert field.annotation == bool
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_str_with_choices_has_literal_annotation():

    class Config(ConfigurationModel):
        str_with_choices_and_default = DjangoModelRef(
            TestModel, "str_with_choices_and_default"
        )

    field = Config.model_fields["str_with_choices_and_default"]

    assert field.title == "str with choices and default"
    assert field.description is None
    assert field.annotation == Literal["foo", "bar"]
    assert field.default == StrChoices.bar
    assert field.is_required() is False


def test_int_with_choices_has_literal_annotation():

    class Config(ConfigurationModel):
        int_with_choices = DjangoModelRef(TestModel, "int_with_choices")

    field = Config.model_fields["int_with_choices"]

    assert field.title == "int with choices"
    assert field.description is None
    assert field.annotation == Literal[1, 8]
    assert field.default == PydanticUndefined
    assert field.is_required() is True


def test_int_with_choices_and_override_has_overridden_annotation():

    class Config(ConfigurationModel):
        int_with_choices: bool = DjangoModelRef(TestModel, "int_with_choices")

    field = Config.model_fields["int_with_choices"]

    assert field.title == "int with choices"
    assert field.description is None
    assert field.annotation == bool
    assert field.default == PydanticUndefined
    assert field.is_required() is True
