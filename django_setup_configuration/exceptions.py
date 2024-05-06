class ConfigurationException(Exception):
    """
    Base exception for configuration steps
    """


class PrerequisiteFailed(ConfigurationException):
    """
    Raises an error when the configuration step can't be started
    """


class ConfigurationRunFailed(ConfigurationException):
    """
    Raises an error when the configuration process was faulty
    """


class SelfTestFailed(ConfigurationException):
    """
    Raises an error for failed configuration self-tests.
    """


class ImproperlyConfigured(ConfigurationException):
    """
    Raised when the library is not properly configured
    """


class DocumentationCheckFailed(ConfigurationException):
    """
    Raised when the documentation based on the configuration models
    is not up to date
    """
