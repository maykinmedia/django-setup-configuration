import difflib
import textwrap
from typing import Literal, Union
from unittest import mock
from unittest.mock import patch

import approvaltests
import pytest
from approvaltests.namer.default_namer_factory import NamerFactory
from bs4 import BeautifulSoup
from docutils import nodes
from docutils.frontend import get_default_settings
from docutils.parsers.rst import Parser, directives
from docutils.utils import new_document
from pydantic import UUID4, Field, ValidationError

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.documentation.setup_config_example import (
    SetupConfigExampleDirective,
)
from django_setup_configuration.documentation.setup_config_usage import (
    SetupConfigUsageDirective,
)
from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from testapp.models import DjangoModel


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
    uuid_field: UUID4 = Field()

    class Meta:
        django_model_refs = {
            DjangoModel: (
                "str_with_choices_and_default",
                "boolean_field",
                "json_with_default_factory",
                "nullable_str",
                "int_with_choices_and_blank_and_non_choice_default",
                "str_with_localized_default",
                "int_with_lazy_default",
                "blank_str",
                "uuid_field_with_default",
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


@pytest.fixture()
def parser():
    return Parser()


@pytest.fixture()
def register_directive():
    directives.register_directive("setup-config-example", SetupConfigExampleDirective)
    directives.register_directive("setup-config-usage", SetupConfigUsageDirective)


@pytest.fixture()
def docutils_document():
    """Fixture to create a new docutils document with complete settings."""
    settings = get_default_settings()

    # Manually add missing settings expected by the directive
    settings.pep_references = False
    settings.rfc_references = False
    settings.env = None  # Sphinx provides `env`, set it to None for testing

    document = new_document("test_document", settings)
    return document


@pytest.mark.usefixtures("register_directive")
def test_directive_output(parser, docutils_document):
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
          uuid_field: 02907e89-1ba8-43e9-a86c-d0534d461316

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

          # POSSIBLE VALUES: ["foo", "bar"]
          # DEFAULT VALUE: "bar"
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

          # POSSIBLE VALUES: [1, 8, 42]
          # DEFAULT VALUE: 42
          # REQUIRED: false
          int_with_choices_and_blank_and_non_choice_default: 42

          # DEFAULT VALUE: "Localized default"
          # REQUIRED: false
          str_with_localized_default: Localized default

          # DEFAULT VALUE: 42
          # REQUIRED: false
          int_with_lazy_default: 42

          # DEFAULT VALUE: ""
          # REQUIRED: false
          blank_str: example_string

          # DEFAULT VALUE: "125a77ef-d158-4bea-b036-8dcdbdde428d"
          # REQUIRED: false
          uuid_field_with_default: 125a77ef-d158-4bea-b036-8dcdbdde428d
    """
    )

    assert len(result) == 1
    assert isinstance(result[0], nodes.block_quote)
    assert_example(result[0].astext(), expected)


@pytest.mark.usefixtures("register_directive")
def test_directive_output_invalid_example_raises_error(parser, docutils_document):
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


@pytest.mark.usefixtures("register_directive")
def test_unsupported_fields(parser, docutils_document):
    rst_content = """
    .. setup-config-example:: tests.test_documentation.UnsupportedConfigStep
    """

    with pytest.raises(ValueError) as excinfo:
        parser.parse(rst_content, docutils_document)

    assert str(excinfo.value) == (
        "Could not generate example for `list_of_primitive_and_complex`. "
        "This directive does not support unions inside lists."
    )


@pytest.mark.usefixtures("register_directive")
def test_usage_directive_output_is_parseable(parser, docutils_document):
    rst_content = """
    .. setup-config-usage::
    """
    parser.parse(rst_content, docutils_document)


def _extract_body(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")
    main_div = soup.find("div", {"class": "body", "role": "main"})
    return str(main_div) if main_div else None


@pytest.mark.sphinx("html", testroot="usage-directive")
@pytest.mark.parametrize(
    "enabled_options,disabled_options",
    [
        pytest.param(set(), set(), id="complete"),
        pytest.param(
            set(),
            {"show_steps"},
            id="steps_fully_disabled",
        ),
        pytest.param(
            set(),
            {"show_steps_toc"},
            id="steps_toc_disabled",
        ),
        pytest.param(
            set(),
            {"show_steps_autodoc"},
            id="steps_autodoc_disabled",
        ),
        pytest.param(
            {"show_steps_toc"},
            {"show_steps"},
            id="steps_disabled_toc_enabled",
        ),
    ],
)
def test_usage_directive_outputs_expected_html_with_sphinx(
    app, disabled_options, enabled_options, request
):
    # Build the rst with options
    rst = ".. setup-config-usage::\n"
    for enabled_option in enabled_options:
        rst += f"    :{enabled_option}: true\n"

    for disabled_option in disabled_options:
        rst += f"    :{disabled_option}: false\n"

    (app.srcdir / "index.rst").write_text(rst)

    # Run Sphinx
    app.build()

    # Validate
    content = (app.outdir / "index.html").read_text(encoding="utf8")

    approvaltests.verify_html(
        _extract_body(content),
        options=NamerFactory.with_parameters(request.node.callspec.id),
    )


@pytest.mark.usefixtures("register_directive")
@mock.patch(
    "django_setup_configuration.documentation.setup_config_usage."
    "SetupConfigUsageDirective._get_django_settings"
)
def test_usage_directive_output_with_no_settings_module_raises(
    m, parser, docutils_document
):
    rst_content = """
    .. setup-config-usage::
    """

    m.return_value = {}
    with pytest.raises(ValueError) as excinfo:
        parser.parse(rst_content, docutils_document)

    assert (
        str(excinfo.value)
        == "Unable to load Django settings. Is DJANGO_SETTINGS_MODULE set?"
    )


@pytest.mark.usefixtures("register_directive")
@mock.patch(
    "django_setup_configuration.documentation.setup_config_usage."
    "SetupConfigUsageDirective._get_django_settings"
)
def test_usage_directive_output_with_missing_steps_raises(m, parser, docutils_document):
    rst_content = """
    .. setup-config-usage::
    """
    m.return_value = {"NOT_SETUP_CONFIGURATION_STEPS": []}

    with pytest.raises(ValueError) as excinfo:
        parser.parse(rst_content, docutils_document)

    assert str(excinfo.value) == (
        "No steps configured. Set SETUP_CONFIGURATION_STEPS via your Django settings."
    )
