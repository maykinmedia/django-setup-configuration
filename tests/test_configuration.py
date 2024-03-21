import pytest

from django_setup_configuration.exceptions import PrerequisiteFailed
from testapp.configuration import UserConfigurationStep


def test_configuration_enabled():
    """
    test that configuration is enabled when the related setting is set to True
    """
    assert UserConfigurationStep().is_enabled() is True


def test_configuration_disabled(settings):
    """
    test that configuration is enabled when the related setting is set to False
    """
    settings.USER_CONFIGURATION_ENABLED = False

    assert UserConfigurationStep().is_enabled() is False


def test_prerequisites_valid():
    """
    test that no error is raised when necessary settings are provided
    """
    UserConfigurationStep().validate_requirements()


def test_prerequisites_invalid(settings):
    """
    test that PrerequisiteFailed is raised when necessary settings are missing
    """
    settings.USER_CONFIGURATION_USERNAME = ""
    settings.USER_CONFIGURATION_PASSWORD = ""

    with pytest.raises(PrerequisiteFailed):
        UserConfigurationStep().validate_requirements()
