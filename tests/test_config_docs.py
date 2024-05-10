from unittest import mock

from django.core.management import call_command

import pytest

from django_setup_configuration.exceptions import DocumentationCheckFailed

from .mocks import mock_product_doc


def test_generate_config_docs(settings):
    content = call_command("generate_config_docs")

    assert "PRODUCT_CONFIG_ENABLE" in content
    # 3 occurrences of PRODUCT_NAME: required, all settings, description
    assert content.count("PRODUCT_NAME") == 3

    assert "PRODUCT_SERVICE_URL" in content
    # 3 occurrences of PRODUCT_SERVICE_URL: required, all settings, description
    assert content.count("PRODUCT_SERVICE_URL") == 3

    assert "PRODUCT_TAGS" in content
    # 2 occurrences of PRODUCT_TAGS: all settings, description
    assert content.count("PRODUCT_TAGS") == 2

    assert "PRODUCT_BOGUS" not in content
    assert "PRODUCT_SERVICE_BOGUS" not in content


def test_check_config_docs_ok(settings):
    with mock.patch("builtins.open", mock.mock_open(read_data=mock_product_doc)):
        call_command("check_config_docs")


def test_check_config_docs_fail_missing_docs(settings):
    mock_open = mock.mock_open(read_data=mock_product_doc)
    mock_open.side_effect = FileNotFoundError

    with mock.patch("builtins.open", mock_open):
        with pytest.raises(DocumentationCheckFailed):
            call_command("check_config_docs")


@mock.patch("testapp.configuration.ProductConfigurationSettings.get_setting_name")
def test_check_config_docs_fail_content_mismatch(m, settings):
    m.return_value = ""

    with pytest.raises(DocumentationCheckFailed):
        call_command("check_config_docs")
