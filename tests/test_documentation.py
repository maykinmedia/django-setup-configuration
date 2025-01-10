import difflib
import textwrap
from typing import Union

import pytest
from docutils import nodes
from docutils.frontend import get_default_settings
from docutils.parsers.rst import Parser, directives
from docutils.utils import new_document
from pydantic import Field

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.documentation.model_directive import (
    PydanticModelExampleDirective,
)
from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from testapp.models import TestModel

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


class TestConfigModel(ConfigurationModel):
    required_int = DjangoModelRef(TestModel, field_name="required_int", examples=[1234])
    int_with_default = DjangoModelRef(TestModel, field_name="int_with_default")
    nullable_and_blank_str = DjangoModelRef(
        TestModel, field_name="nullable_and_blank_str"
    )
    field_with_help_text = DjangoModelRef(TestModel, field_name="field_with_help_text")
    # TODO is this positioned correctly within the result?
    array_field_with_default: list = DjangoModelRef(
        TestModel, field_name="array_field_with_default"
    )
    array_field: list[NestedConfigurationModel] = DjangoModelRef(
        TestModel, field_name="array_field"
    )
    union_of_models: Union[NestedConfigurationModel, NestedConfigurationModel2] = Field(
        description="union of models"
    )
    union_of_models2: NestedConfigurationModel | NestedConfigurationModel2 = Field(
        description="union of models with |"
    )
    union_of_primitives: Union[str, int] = Field()

    class Meta:
        django_model_refs = {
            TestModel: (
                "str_with_choices_and_default",
                "boolean_field",
                "json_with_default_factory",
            )
        }


class TestConfigStep(BaseConfigurationStep[TestConfigModel]):
    config_model = TestConfigModel
    verbose_name = "Test config"

    namespace = "test_config"
    enable_setting = "test_config_enable"


@pytest.fixture
def register_directive():
    directives.register_directive(
        "pydantic-model-example", PydanticModelExampleDirective
    )


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


def test_my_directive_output(register_directive, docutils_document):
    # Create a parser and simulate a directive
    rst_content = """
    .. pydantic-model-example:: tests.test_documentation.TestConfigStep
    """

    # Parse the content
    parser.parse(rst_content, docutils_document)

    # Retrieve the generated nodes
    result = docutils_document.children

    expected = textwrap.dedent(
        """\
        test_config_enable: true
        test_config:

          # DEFAULT VALUE: [{'foo': 'bar'}, {'foo': 'baz'}]
          # REQUIRED: False
          array_field_with_default:
            - foo: bar
            - foo: baz

          # REQUIRED: False
          array_field:
            -

              # DESCRIPTION: Nested description
              # DEFAULT VALUE: bar
              # REQUIRED: False
              foo: baz

          # DESCRIPTION: union of models
          # REQUIRED: True
          # This value is polymorphic, the possible values are divided by dashes
          # and only one of them can be commented out.
          # -------------OPTION 1-------------
          # union_of_models:
          #   # DESCRIPTION: Nested description2
          #   # DEFAULT VALUE: 1
          #   # REQUIRED: False
          #   bar: 1234
          # -------------OPTION 2-------------
          union_of_models:

            # DESCRIPTION: Nested description
            # DEFAULT VALUE: bar
            # REQUIRED: False
            foo: baz

          # DESCRIPTION: union of models with |
          # REQUIRED: True
          # This value is polymorphic, the possible values are divided by dashes
          # and only one of them can be commented out.
          # -------------OPTION 1-------------
          # union_of_models2:
          #   # DESCRIPTION: Nested description2
          #   # DEFAULT VALUE: 1
          #   # REQUIRED: False
          #   bar: 1234
          # -------------OPTION 2-------------
          union_of_models2:

            # DESCRIPTION: Nested description
            # DEFAULT VALUE: bar
            # REQUIRED: False
            foo: baz

          # REQUIRED: True
          # This value is polymorphic, the possible values are divided by dashes
          # and only one of them can be commented out.
          # -------------OPTION 1-------------
          # union_of_primitives: 123
          # -------------OPTION 2-------------
          union_of_primitives: example_string

          # REQUIRED: True
          required_int: 1234

          # DEFAULT VALUE: 42
          # REQUIRED: False
          int_with_default: 42

          # REQUIRED: False
          nullable_and_blank_str: example_string

          # DESCRIPTION: This is the help text
          # REQUIRED: True
          field_with_help_text: 123

          # DEFAULT VALUE: bar
          # POSSIBLE VALUES: ('foo', 'bar')
          # REQUIRED: False
          str_with_choices_and_default: bar

          # DEFAULT VALUE: True
          # REQUIRED: False
          boolean_field: true

          # DEFAULT VALUE: {'foo': 'bar'}
          # REQUIRED: False
          json_with_default_factory:
            foo: bar
    """
    )

    assert len(result) == 1
    assert isinstance(result[0], nodes.block_quote)
    assert_example(result[0].astext(), expected)
