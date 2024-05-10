import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent

SECRET_KEY = "so-secret-i-cant-believe-you-are-looking-at-this"

USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django_setup_configuration",
    "testapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "testapp.urls"

#
# django-setup-configuration settings
#
SETUP_CONFIGURATION_STEPS = ["testapp.configuration.UserConfigurationStep"]


#
# testapp settings
#
USER_CONFIGURATION_ENABLED = os.getenv("USER_CONFIGURATION_ENABLED", True)
USER_CONFIGURATION_USERNAME = os.getenv("USER_CONFIGURATION_USERNAME", "demo")
USER_CONFIGURATION_PASSWORD = os.getenv("USER_CONFIGURATION_PASSWORD", "secret")

DJANGO_SETUP_CONFIG_REGISTER = [
    {
        "model": "testapp.configuration.ProductConfigurationSettings",
        "file_name": "product",
    }
]
DJANGO_SETUP_CONFIG_TEMPLATE_NAME = "testapp/config_doc.rst"
DJANGO_SETUP_CONFIG_DOC_DIR = "testapp/docs/configuration"
