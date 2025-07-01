import warnings

from django.contrib.auth import get_user_model

import pytest

from django_setup_configuration.contrib.auth.steps import UserConfigurationStep
from django_setup_configuration.test_utils import execute_single_step


@pytest.fixture()
def yaml_file_with_admin_configuration(yaml_file_factory):

    yaml_file = yaml_file_factory(
        {
            "default_user_configuration_enable": True,
            "default_user_configuration_config": {
                "users": [
                    {
                        "email": "admin@staffuser.nl",
                        "username": "admin",
                        "is_staff": True,
                        "is_superuser": True,
                        "password": "change_me",
                    },
                ],
            },
        }
    )

    return yaml_file


@pytest.fixture()
def yaml_file_with_admin_configuration_alternative(yaml_file_factory):

    yaml_file = yaml_file_factory(
        {
            "default_user_configuration_enable": True,
            "default_user_configuration_config": {
                "users": [
                    {
                        "email": "formeradmin.newemail@admin.nl",
                        "username": "admin",
                        "is_staff": False,
                        "is_superuser": False,
                        "password": "change_me",
                    },
                ],
            },
        }
    )

    return yaml_file


@pytest.fixture()
def yaml_file_with_admin_configuration_username_changed(yaml_file_factory):
    yaml_file = yaml_file_factory(
        {
            "default_user_configuration_enable": True,
            "default_user_configuration_config": {
                "users": [
                    {
                        "email": "admin@staffuser.nl",
                        "username": "new_admin_username",
                        "is_staff": False,
                        "is_superuser": False,
                        "password": "change_me",
                    },
                ],
            },
        }
    )

    return yaml_file


@pytest.fixture()
def yaml_file_with_admin_configuration_multiple_users(yaml_file_factory):

    yaml_file = yaml_file_factory(
        {
            "default_user_configuration_enable": True,
            "default_user_configuration_config": {
                "users": [
                    {
                        "email": "admin@staffuser.nl",
                        "username": "admin",
                        "is_staff": False,
                        "is_superuser": False,
                        "password": "change_me",
                    },
                    {
                        "email": "test@user.nl",
                        "username": "testuser",
                        "is_staff": False,
                        "is_superuser": False,
                        "password": "change_me",
                    },
                ],
            },
        }
    )

    return yaml_file


@pytest.mark.django_db
def test_load_step_config_from_source_user_is_created(
    yaml_file_with_admin_configuration,
):
    with pytest.warns(UserWarning):
        execute_single_step(
            UserConfigurationStep, yaml_source=yaml_file_with_admin_configuration
        )

    User = get_user_model()

    assert User.objects.count() == 1
    username = "admin"

    password = "change_me"

    user = User.objects.get(username=username)
    assert user.check_password(password)

    assert list(
        User.objects.values_list("username", "email", "is_staff", "is_superuser")
    ) == [("admin", "admin@staffuser.nl", True, True)]


@pytest.mark.django_db
def test_load_step_config_with_multiple_users(
    yaml_file_with_admin_configuration,
    yaml_file_with_admin_configuration_multiple_users,
):

    # First run, create an initial admin user
    execute_single_step(
        UserConfigurationStep, yaml_source=yaml_file_with_admin_configuration
    )

    User = get_user_model()

    assert User.objects.count() == 1

    admin_user = User.objects.get(username="admin")
    assert admin_user.is_staff
    assert admin_user.is_superuser

    # Then, update the initial admin user, and also add a new user
    execute_single_step(
        UserConfigurationStep,
        yaml_source=yaml_file_with_admin_configuration_multiple_users,
    )

    assert User.objects.count() == 2

    # Verify the (existing) admin user was updated
    admin_user.refresh_from_db()
    assert not admin_user.is_staff
    assert not admin_user.is_superuser

    # Verify a new user was created
    new_user = User.objects.get(username="testuser")
    assert new_user.email == "test@user.nl"


@pytest.mark.django_db
def test_load_step_config_from_source_user_is_updated(
    yaml_file_with_admin_configuration, yaml_file_with_admin_configuration_alternative
):
    execute_single_step(
        UserConfigurationStep, yaml_source=yaml_file_with_admin_configuration
    )

    User = get_user_model()

    email = "admin@staffuser.nl"
    username = "admin"

    assert list(
        User.objects.values_list("username", "email", "is_staff", "is_superuser")
    ) == [(username, email, True, True)]

    execute_single_step(
        UserConfigurationStep,
        yaml_source=yaml_file_with_admin_configuration_alternative,
    )

    new_email = "formeradmin.newemail@admin.nl"
    assert list(User.objects.values_list("email", "is_staff", "is_superuser")) == [
        (new_email, False, False)
    ]


@pytest.mark.django_db
def test_warning_is_only_emitted_on_default_password(
    yaml_file_with_admin_configuration,
):
    # Verify that a warning was raised
    with pytest.warns(UserWarning):
        execute_single_step(
            UserConfigurationStep, yaml_source=yaml_file_with_admin_configuration
        )

    User = get_user_model()

    username = "admin"
    user = User.objects.get(username=username)

    user.set_password("12345")
    user.save()

    # After password change, no warning should be raised:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        execute_single_step(
            UserConfigurationStep, yaml_source=yaml_file_with_admin_configuration
        )


@pytest.mark.django_db
def test_load_step_config_from_source_user_is_updated_with_username(
    yaml_file_with_admin_configuration,
    yaml_file_with_admin_configuration_username_changed,
):
    """
    Verifies whether the step still works if not
    'username' but 'email' is set as the USERNAME_FIELD.
    """

    User = get_user_model()
    User.USERNAME_FIELD = "email"

    execute_single_step(
        UserConfigurationStep, yaml_source=yaml_file_with_admin_configuration
    )

    email = "admin@staffuser.nl"
    username = "admin"

    user = User.objects.get(email=email)

    assert user.username == username

    execute_single_step(
        UserConfigurationStep,
        yaml_source=yaml_file_with_admin_configuration_username_changed,
    )

    user.refresh_from_db()

    new_username = "new_admin_username"
    assert user.username == new_username
