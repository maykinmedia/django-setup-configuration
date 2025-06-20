import warnings

from django.contrib.auth import get_user_model

from django_setup_configuration.configuration import BaseConfigurationStep

from .models import UserConfigurationModel

User = get_user_model()


class UserConfigurationStep(BaseConfigurationStep):
    """
    Creates or updates one or more default users based on
    YAML settings. Note that a provided password
    will only be used if the user does not exist yet.
    """

    verbose_name = "User Configuration Step"
    enable_setting = "default_user_configuration_enable"
    config_model = UserConfigurationModel
    namespace = "default_user_configuration_config"

    def execute(self, model):

        for user_item in model.users:

            User = get_user_model()
            username_field = User.USERNAME_FIELD
            username_value = getattr(user_item, username_field)

            defaults = {
                "is_staff": user_item.is_staff,
                "is_superuser": user_item.is_superuser,
            }

            if username_field != "email":
                defaults["email"] = user_item.email

            if username_field != "username":
                defaults["username"] = user_item.username

            user, created = User.objects.update_or_create(
                **{username_field: username_value}, defaults=defaults
            )

            if created:
                user.set_password(user_item.password)

            user.save()

            if user.check_password(user_item.password):
                warnings.warn(
                    "\nThe password for the automatically created "
                    f"user {username_value} is currently set to a hardcoded default. "
                    "Make sure to change the password in the admin panel.\n\n"
                )
