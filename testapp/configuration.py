from django.contrib.auth.models import User

from django_setup_configuration import BaseConfigurationStep, ConfigurationModel


class UserConfigurationModel(ConfigurationModel):

    class Meta:
        django_model_refs = {
            User: [
                "username",
                "password",
            ]
        }


class UserConfigurationStep(BaseConfigurationStep[UserConfigurationModel]):
    """
    Set up an initial user.
    """

    config_model = UserConfigurationModel
    enable_setting = "user_configuration_enabled"
    namespace = "user_configuration"
    verbose_name = "User Configuration"

    def execute(self, model) -> None:
        user_qs = User.objects.filter(username=model.username)
        if user_qs.exists():
            user = user_qs.get()
            if not user.check_password(model.password):
                user.set_password(model.password)
                user.save()

        else:
            user = User.objects.create_user(
                username=model.username,
                password=model.password,
                is_superuser=True,
            )
