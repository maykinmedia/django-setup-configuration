Configuration documentation
===========================

The library can generate (and check) the documentation for model fields which are being
configured, containing information about the names of the fields, possible values,
default values, and a short description. This helps clients determine what can be
configured with the help of the library and how.


Setup
"""""

Start by defining the target directory of the docs and the template that will be used
to render them. For example:

::

    DJANGO_SETUP_CONFIG_TEMPLATE_NAME = "configurations/config_doc.rst"
    DJANGO_SETUP_CONFIG_DOC_DIR = "docs/configuration"

Next, create a template:

::

    {% block link %}{{ link }}{% endblock %}

    {% block title %}{{ title }}{% endblock %}

    Settings Overview
    =================

    Enable/Disable configuration:
    """""""""""""""""""""""""""""

    ::

        {% spaceless %}
        {{ enable_settings }}
        {% endspaceless %}

    Required:
    """""""""

    ::

        {% spaceless %}
        {% for setting in required_settings %}{{ setting }}
        {% endfor %}
        {% endspaceless %}

    All settings:
    """""""""""""

    ::

        {% spaceless %}
        {% for setting in all_settings %}{{ setting }}
        {% endfor %}
        {% endspaceless %}

    Detailed Information
    ====================

    ::

        {% spaceless %}
        {% for detail in detailed_info %}
        {% for part in detail %}{{ part|safe }}
        {% endfor %}{% endfor %}
        {% endspaceless %}

You're free to choose a different layout, of course, but this should give you an idea
of what's available, and some of the nuisances (like spacing) you might run into.

The value for ``link`` is automatically create based on the ``file_name`` you defined
in the first step. Similarly, ``enable_settings`` is automatically created. Values for
the other template variables are determined based on the model your client is configuring,
and a related settings model you need to define.

Generally, when adding support for configuring a model ``FooConfiguration`` with
``django-setup-configuration``, you will have a class ``FooConfigurationStep(BaseConfigurationStep)``
that carries out the configuration. In the same file, define a class with information about
the fields from ``FooConfiguration`` that are required, included, or excluded, and
meta-information required for creating the docs. For example:


::

    from django-setup-configuration import ConfigSettingsModel

    class FooConfigurationSettings(ConfigSettingsModel):
        model = FooConfiguration
        display_name = "Foo Configuration"
        namespace = "FOO"
        required_fields = (
            "bar",
            "baz",
        )
        included_fields =  required_fields + (
            "foobar",
        )
        excluded_fields = (
            "bogus",
        )


    class FooConfigurationStep(BaseConfigurationStep):
        ...

``display_name`` provides the value for ``title`` in the template above. ``namespace``
tells you how config variables for different models are namespaced. In your settings,
you would define ``FOO_BAR``, ``FOO_BAZ``, and ``FOO_FOOBAR``.

Finally, you need to register you configuration settings class with the library:

::

    DJANGO_SETUP_CONFIG_REGISTER = [
        {
            "model": "example_project.path.to.FooConfigurationSettings",
            "file_name": "foo_config",
        }
    ]


Usage
"""""

The library provides two management commands:

::

    manage.py generate_config_docs [CONFIG_OPTION]
    manage.py check_config_docs

The optional ``CONFIG_OPTION`` should be a ``file_name`` (without extension) that
corresponds to a settings model (e.g. ``foo_config``). When given,
``generate_config_docs`` will create the docs for the corresponding model. Otherwise
the command creates docs for all supported models. ``check_config_docs`` is similar
to ``manage.py makemigrations --check --dry-run``: it tests that documentation for your
configuration setup steps exists and is accurate (if you make changes to
``FooConfiguration`` or ``FooConfigurationSettings`` without re-creating the docs,
``check_config_docs`` will raise an exception).
