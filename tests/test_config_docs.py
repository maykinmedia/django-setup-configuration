from unittest import mock

from django.core.management import call_command

import pytest

from django_setup_configuration.exceptions import DocumentationCheckFailed

from .mocks import mock_user_doc, mock_user_doc_mismatch

open_func = "django_setup_configuration.management.commands.generate_config_docs.open"


def test_generate_config_docs_new_file(settings):
    """
    Assert that file with correct content is written if no docs exist
    """
    open_mock = mock.mock_open()

    with mock.patch(open_func, open_mock):
        call_command("generate_config_docs")

    open_mock.assert_called_with("testapp/docs/configuration/user.rst", "w+")
    open_mock.return_value.write.assert_called_once_with(mock_user_doc)


def test_generate_config_docs_content_mismatch(settings):
    """
    Assert that file with updated content is written if the content read by `open`
    is different
    """
    open_mock = mock.mock_open(read_data=mock_user_doc_mismatch)

    with mock.patch(open_func, open_mock):
        call_command("generate_config_docs")

    open_mock.assert_called_with("testapp/docs/configuration/user.rst", "w+")
    open_mock.return_value.write.assert_called_once_with(mock_user_doc)


def test_generate_config_docs_dry_run(settings):
    """
    Assert that an Exception is raised if stale content is detected by a dry-run
    """
    open_mock = mock.mock_open(read_data=mock_user_doc_mismatch)

    with mock.patch(open_func, open_mock):
        with pytest.raises(DocumentationCheckFailed):
            call_command("generate_config_docs", "--dry-run")

    assert (
        mock.call("testapp/docs/configuration/user.rst", "w+")
        not in open_mock.mock_calls
    )


def test_docs_up_to_date(settings):
    """
    Assert that no file is written if the content read by `open` is up to date
    """
    open_mock = mock.mock_open(read_data=mock_user_doc)

    with mock.patch(open_func, open_mock):
        call_command("generate_config_docs")

    assert (
        mock.call("testapp/docs/configuration/user.rst", "w+")
        not in open_mock.mock_calls
    )
