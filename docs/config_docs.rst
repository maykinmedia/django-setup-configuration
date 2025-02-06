.. _config_docs:

Configuration Documentation
===========================

The library provides two Sphinx directives:

1. ``setup-config-example`` - Generates (and validates) an example configuration file in YAML format for a given ``ConfigurationStep``. This includes information about field names, possible values, default values, and descriptions, helping clients understand available configuration options.

2. ``setup-config-usage`` - Generates basic usage information and lists all configured steps with metadata and example YAMLs (it does this by wrapping ``setup-config-example`` so the examples will be validated as well). This provides a complete overview for users who want to bootstrap their installation.

Using setup-config-example
--------------------------

First, add the extension and its requirements to ``conf.py`` in your documentation directory:

.. code-block:: python

    extensions = [
        ...
        "sphinx.ext.autodoc",
        "django_setup_configuration.documentation.setup_config_example",
        ...
    ]


Then display a YAML example using the directive:

.. code-block:: rst

    .. setup-config-example:: path.to.your.ConfigurationStep

This will produce output similar to the following example (using the ``SitesConfigurationStep`` provided by this library):

.. setup-config-example:: django_setup_configuration.contrib.sites.steps.SitesConfigurationStep

.. warning::

    Not all configurations are currently supported by this directive.
    Complex type annotations like ``list[ComplexObject | ComplexObject]`` will raise errors during documentation build.

Using setup-config-usage
------------------------

First, add the extension and its requirements to ``conf.py`` in your documentation directory:

.. code-block:: python

    extensions = [
        ...
        "sphinx.ext.autodoc",
        "django_setup_configuration.documentation.setup_config_example",
        "django_setup_configuration.documentation.setup_config_usage",
        ...
    ]

To use this directive, you'll also have to ensure Django is configured and initialized
in your Sphinx `conf.py` file, for instance like this:

.. code-block:: python

    # docs/conf.py

    # ...
    import django
    from django.conf import settings
        
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_settings_module")
    django.setup()

    # ...
    # extensions = [...]

Then display usage information using the directive:

.. code-block:: rst

    .. setup-config-usage::
        

This generates a "how to" introduction for invoking the management command, 
followed by sections for each configured step with example YAML configurations.

By default, the directive will output a full documentation page, but you can hide individual
sections using the following options:

- ``show_command_usage``: whether to include basic usage information on how to invoke the management command
- ``show_steps``: whether to display information about the configured steps
- ``show_steps_toc``: whether to include a short table of contents of all configured steps, before displaying the individual step sections
- ``show_steps_autodoc``: whether to include an ``autodoc`` section showing the full path to the step module

For example, to hide the usage section, show the steps without autodoc:

.. code-block:: rst

    .. setup-config-usage::
        :show_command_usage: false
        :show_steps_autodoc: false


.. note::

    The titles for the step sections will be taken from the step's ``verbose_title`` field,
    whereas the descriptions are taken from the step class's docstring (if present).