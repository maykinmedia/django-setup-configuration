import difflib
import textwrap
from typing import Literal, Union
from unittest.mock import patch

import pytest
from docutils import nodes
from docutils.frontend import get_default_settings
from docutils.parsers.rst import Parser, directives
from docutils.utils import new_document
from pydantic import Field, ValidationError

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.documentation.setup_config_example import (
    SetupConfigExampleDirective,
)
from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from testapp.models import DjangoModel

parser = Parser()


class NestedConfigurationModel(ConfigurationModel):
    foo: str = Field(description="Nested description", default="bar", examples=["baz"])


class NestedConfigurationModel2(ConfigurationModel):
    bar: int = Field(description="Nested description2", default=1, examples=[1234])


def assert_example(actual, expected):
    assert actual == expected, "\n".join(
        difflib.unified_diff(
            actual.splitlines(),
            expected.splitlines(),
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )
    )


class ConfigModel(ConfigurationModel):
    required_int = DjangoModelRef(
        DjangoModel, field_name="required_int", examples=[1234]
    )
    int_with_default = DjangoModelRef(DjangoModel, field_name="int_with_default")
    nullable_and_blank_str = DjangoModelRef(
        DjangoModel, field_name="nullable_and_blank_str"
    )
    field_with_help_text = DjangoModelRef(
        DjangoModel, field_name="field_with_help_text"
    )
    # TODO is this positioned correctly within the result?
    array_field_with_default: list = DjangoModelRef(
        DjangoModel, field_name="array_field_with_default"
    )
    array_field: list[NestedConfigurationModel] = DjangoModelRef(
        DjangoModel, field_name="array_field"
    )
    union_of_models: Union[NestedConfigurationModel, NestedConfigurationModel2] = Field(
        description="union of models"
    )
    union_of_models2: NestedConfigurationModel | NestedConfigurationModel2 = Field(
        description="union of models with |"
    )
    union_of_primitives: Union[str, int] = Field()
    sequence_of_primitives: list[int] = Field()
    literal: Literal["foo", "bar", "bar"] = Field()
    literal_block_scalar: str = Field(default='{\n  "foo":"bar",\n  "bar":"baz"\n}')

    class Meta:
        django_model_refs = {
            DjangoModel: (
                "str_with_choices_and_default",
                "boolean_field",
                "json_with_default_factory",
                "nullable_str",
            )
        }
        extra_kwargs = {
            "nullable_str": {"examples": ["example string via extra kwargs"]}
        }


class ConfigStep(BaseConfigurationStep[ConfigModel]):
    config_model = ConfigModel
    verbose_name = "Test config"

    namespace = "test_config"
    enable_setting = "test_config_enable"


class UnsupportedConfigModel(ConfigurationModel):
    list_of_primitive_and_complex: list[NestedConfigurationModel | str] = Field()


class UnsupportedConfigStep(BaseConfigurationStep[UnsupportedConfigModel]):
    config_model = UnsupportedConfigModel
    verbose_name = "Unsupported Test config"

    namespace = "unsupported_test_config"
    enable_setting = "unsupported_test_config_enable"


@pytest.fixture
def register_directive():
    directives.register_directive("setup-config-example", SetupConfigExampleDirective)


@pytest.fixture
def docutils_document():
    """Fixture to create a new docutils document with complete settings."""
    settings = get_default_settings()

    # Manually add missing settings expected by the directive
    settings.pep_references = False
    settings.rfc_references = False
    settings.env = None  # Sphinx provides `env`, set it to None for testing

    document = new_document("test_document", settings)
    return document


def test_directive_output(register_directive, docutils_document):
    rst_content = """
    .. setup-config-example:: tests.test_documentation.ConfigStep
    """

    # Parse the content
    parser.parse(rst_content, docutils_document)

    # Retrieve the generated nodes
    result = docutils_document.children

    expected = textwrap.dedent(
        """\
        test_config_enable: true
        test_config:

          # DEFAULT VALUE: [{"foo": "bar"}, {"foo": "baz"}]
          # REQUIRED: false
          array_field_with_default:
            - foo: bar
            - foo: baz

          # DEFAULT VALUE: null
          # REQUIRED: false
          array_field:
            -

              # DESCRIPTION: Nested description
              # DEFAULT VALUE: "bar"
              # REQUIRED: false
              foo: baz

          # DESCRIPTION: union of models
          # REQUIRED: true
          # This field can have multiple different kinds of value. All the
          # alternatives are listed below and are divided by dashes. Only **one of
          # them** can be commented out.
          # -------------ALTERNATIVE 1-------------
          # union_of_models:
          #   # DESCRIPTION: Nested description2
          #   # DEFAULT VALUE: 1
          #   # REQUIRED: false
          #   bar: 1234
          # -------------ALTERNATIVE 2-------------
          union_of_models:

            # DESCRIPTION: Nested description
            # DEFAULT VALUE: "bar"
            # REQUIRED: false
            foo: baz

          # DESCRIPTION: union of models with |
          # REQUIRED: true
          # This field can have multiple different kinds of value. All the
          # alternatives are listed below and are divided by dashes. Only **one of
          # them** can be commented out.
          # -------------ALTERNATIVE 1-------------
          # union_of_models2:
          #   # DESCRIPTION: Nested description2
          #   # DEFAULT VALUE: 1
          #   # REQUIRED: false
          #   bar: 1234
          # -------------ALTERNATIVE 2-------------
          union_of_models2:

            # DESCRIPTION: Nested description
            # DEFAULT VALUE: "bar"
            # REQUIRED: false
            foo: baz

          # REQUIRED: true
          # This field can have multiple different kinds of value. All the
          # alternatives are listed below and are divided by dashes. Only **one of
          # them** can be commented out.
          # -------------ALTERNATIVE 1-------------
          # union_of_primitives: 123
          # -------------ALTERNATIVE 2-------------
          union_of_primitives: example_string

          # REQUIRED: true
          sequence_of_primitives:
            - 123

          # POSSIBLE VALUES: ["foo", "bar"]
          # REQUIRED: true
          literal: foo

          # DEFAULT VALUE: {
          #   "foo":"bar",
          #   "bar":"baz"
          # }
          # REQUIRED: false
          literal_block_scalar: |-
            {
              "foo":"bar",
              "bar":"baz"
            }

          # REQUIRED: true
          required_int: 1234

          # DEFAULT VALUE: 42
          # REQUIRED: false
          int_with_default: 42

          # DEFAULT VALUE: null
          # REQUIRED: false
          nullable_and_blank_str: example_string

          # DESCRIPTION: This is the help text
          # REQUIRED: true
          field_with_help_text: 123

          # DEFAULT VALUE: "bar"
          # POSSIBLE VALUES: ["foo", "bar"]
          # REQUIRED: false
          str_with_choices_and_default: bar

          # DEFAULT VALUE: true
          # REQUIRED: false
          boolean_field: true

          # DEFAULT VALUE: {"foo": "bar"}
          # REQUIRED: false
          json_with_default_factory:
            foo: bar

          # DEFAULT VALUE: null
          # REQUIRED: false
          nullable_str: example string via extra kwargs
    """
    )

    assert len(result) == 1
    assert isinstance(result[0], nodes.block_quote)
    assert_example(result[0].astext(), expected)


def test_directive_output_invalid_example_raises_error(
    register_directive, docutils_document
):
    # The example for `ConfigModel` will not be valid if every example is a string
    with patch(
        (
            "django_setup_configuration.documentation."
            "setup_config_example._generate_model_example"
        ),
        return_value="invalid",
    ):
        rst_content = """
        .. setup-config-example:: tests.test_documentation.ConfigStep
        """

        with pytest.raises(ValidationError):
            # Parse the content, should raise a `ValidationError`
            # because the example is incorrect
            parser.parse(rst_content, docutils_document)


def test_unsupported_fields(register_directive, docutils_document):
    rst_content = """
    .. setup-config-example:: tests.test_documentation.UnsupportedConfigStep
    """

    with pytest.raises(ValueError) as excinfo:
        parser.parse(rst_content, docutils_document)

    assert str(excinfo.value) == (
        "Could not generate example for `list_of_primitive_and_complex`. "
        "This directive does not support unions inside lists."
    )
