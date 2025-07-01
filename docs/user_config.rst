=======================================================
``django.contrib.auth.UserConfiguration`` configuration
=======================================================

.. autoclass:: django_setup_configuration.contrib.auth.steps.UserConfigurationStep
    :noindex:

To make use of this, add the step to your ``SETUP_CONFIGURATION_STEPS``:

    .. code-block:: python

        SETUP_CONFIGURATION_STEPS = [
            ...
            "django_setup_configuration.contrib.auth.steps.UserConfigurationStep",
            ...
        ]

Create or update your YAML configuration file with your settings:

    .. code-block:: yaml

        default_user_configuration_enable: true
        default_user_configuration_config:
          users:
            - email: example@user.nl
              username: foo
              is_staff: True
              is_superuser: True
              password: change_me

.. note::
    This step assumes your User model is based on ``django.contrib.auth.models.AbstractUser`` 
    (though it need not actually inherit from it, as long as it has ``USERNAME_FIELD`` set and 
    contains the required fields).

    Furthermore, ``AbstractUser.USERNAME_FIELD`` must be set to either ``email`` or ``username``.

    Lastly, note that the ``password`` field is meant to be a default and should be changed 
    as soon as possible after the user has been created. It also cannot be used to override 
    the password of an existing user, as it will only be used when creating a new user, not 
    when updating it.