Configuration documentation
===========================

The library can generate (and check) the documentation for model fields which are being
configured, containing information about the names of the fields, possible values,
default values, and a short description. This helps clients determine what can be
configured with the help of the library and how.


Setup
"""""

Start by defining the target directory where the docs will be saved and the template used
to render them (a default template is included, but you can specify your own). For example:

::

    DJANGO_SETUP_CONFIG_TEMPLATE = "django-setup-configuration/config_doc.rst"
    DJANGO_SETUP_CONFIG_DOC_PATH = "your-project/docs/configuration"

Only a subset of Django model fields (CharField, TextField...) is supported out of the box.
The reason for this is two-fold. On the one hand, there are many custom model fields from various
third-party libraries, and it is impossible to support documentation for all of them.
Secondly, the exact way how certain fields are configured via strings (the values of configuration
variables) inevitably depends on the implementation. For example, in order to configure a
``DateTimeField`` via a string provided by the end user, the string has to be converted to a Python
``datetime`` object. How this is done (in particular, what format of string is tolerated) depends on
the implementation of the configuration step and cannot be anticipated by the library. For a list of
currently supported fields, see the list of constants defined in the source code:
`link <https://github.com/maykinmedia/django-setup-configuration/tree/main/django_setup_configuration/>`_

You can add support for additional fields like ``FileField`` or custom fields from third-party
libraries (or your own) as follows:

::

    DJANGO_SETUP_CONFIG_CUSTOM_FIELDS = [
        {
            "field": "django_jsonform.models.fields.ArrayField",
            "description": "string, comma-delimited ('foo,bar,baz')",
        },
        {
            "field": "django.db.models.fields.files.FileField",
            "description": "string represeting the (absolute) path to a file, including file extension",
        },
    ]


Usage
"""""

For every configuration step, define a ``ConfigSetting`` model with the appropriate settings as
attribute on the class:

::

        from django-setup-configuration.config_settings import ConfigSettingsModel
        from django-setup-configuration.models import BaseConfigurationStep

        FooConfigurationStep(BaseConfigurationStep):
            verbose_name = "Configuration step for Foo"
            config_settings = ConfigSettings(
                enable_setting = "FOO_CONFIG_ENABLE"
                namespace="FOO",
                file_name="foo",
                models=["FooConfigurationModel"],
                required_settings=[
                    "FOO_SOME_SETTING",
                    "FOO_SOME_OTHER_SETTING",
                ],
                optional_settings=[
                    "FOO_SOME_OPT_SETTING",
                    "FOO_SOME_OTHER_OPT_SETTING",
                ],
                independent=True,
                related_config_settings=[
                    "BarRelatedConfigurationStep.config_settings",
                ],
                additional_info={
                    "example_non_model_field": {
                        "variable": "FOO_EXAMPLE_NON_MODEL_FIELD",
                        "description": "Documentation for a field that could not
                            be retrievend from a model",
                        "possible_values": "string (URL)",
                    },
                },
            )

            def configure(): ...

The documentation for settings used to configure Django model fields is pulled from the help
text of the relevant fields. You merely have to specify the models used in the configuration
step and which settings are required/optional. ``additional_info`` is used to manually document
configuration settings which are not associated with any model field.

In certain cases, you may want to avoid creating a separate documentation file for some
configuration steps. For example, you may want to include the documentation for API services
associated with ``FOO`` in the documentation for ``FOO``, instead of having a separate file
for each. In this case, you set ``independent`` to ``False`` on the ``ConfigSettings`` that you
want to embed, and include the relevant ``ConfigSettings`` under ``related_config_settings``
on your main config.

With everything set up, you can generate the docs with the following command:

::

    python manage.py generate_config_docs

The command can be run with a ``--dry-run`` option to only check if the docs are up-to-date and
raise an error if they are not (this could be part of your CI):

::

    python manage.py generate_config_docs --dry-run
