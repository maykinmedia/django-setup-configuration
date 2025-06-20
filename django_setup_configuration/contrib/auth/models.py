from django.contrib.auth import get_user_model

from django_setup_configuration.models import ConfigurationModel

User = get_user_model()


class UserConfigurationItem(ConfigurationModel):
    """
    Configuration model for a setting standard default users. Note that
    this is based on the fields in AbstractUser and will not
    work with other custom User models. Also, the
    'USERNAME_FIELD' must be set to either the username or the email.
    """

    class Meta:
        django_model_refs = {
            User: (
                "email",
                "username",
                "password",
                "is_staff",
                "is_superuser",
            )
        }


class UserConfigurationModel(ConfigurationModel):
    users: list[UserConfigurationItem]
