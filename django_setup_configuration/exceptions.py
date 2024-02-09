class ConfigurationException(Exception):
    """
    Base exception for configuration steps
    """


class PrerequisiteFailed(ConfigurationException):
    """
    Raise an error then configuration step can't be started
    """


class ConfigurationRunFailed(ConfigurationException):
    """
    Raise an error then configuration process was faulty
    """


class SelfTestFailed(ConfigurationException):
    """
    Raise an error for failed configuration self-tests.
    """
