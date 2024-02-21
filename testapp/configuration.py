from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import SelfTestFailed


class UserConfigurationStep(BaseConfigurationStep):
    """
    Set up an initial user

    The configuration set up a particular user only once in the regular mode.
    If you want to change password or permissions use 'overwrite' mode
    """

    verbose_name = "User Configuration"
    required_settings = ["USER_CONFIGURATION_USERNAME", "USER_CONFIGURATION_PASSWORD"]
    enable_setting = "USER_CONFIGURATION_ENABLED"

    def is_configured(self) -> bool:
        return User.objects.filter(
            username=settings.USER_CONFIGURATION_USERNAME
        ).exists()

    def configure(self) -> None:
        user_qs = User.objects.filter(username=settings.USER_CONFIGURATION_USERNAME)
        if user_qs.exists():
            user = user_qs.get()
            if not user.check_password(settings.USER_CONFIGURATION_PASSWORD):
                user.set_password(settings.USER_CONFIGURATION_PASSWORD)
                user.save()

        else:
            User.objects.create_user(
                username=settings.USER_CONFIGURATION_USERNAME,
                password=settings.USER_CONFIGURATION_PASSWORD,
                is_superuser=True,
            )

    def test_configuration(self) -> None:
        user = authenticate(
            username=settings.USER_CONFIGURATION_USERNAME,
            password=settings.USER_CONFIGURATION_PASSWORD,
        )
        if not user:
            raise SelfTestFailed("No user with provided credentials is found")
