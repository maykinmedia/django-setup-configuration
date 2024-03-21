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
