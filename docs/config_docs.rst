.. _config_docs:

Configuration documentation
===========================

The library provides a Sphinx directive that generates (and validates) an example configuration
file in YAML format for a given ``ConfigurationStep``, containing information about the names of the fields,
possible values, default values, and a short description. This helps clients determine
what can be configured with the help of the library and how.


Setup
"""""

Start by adding the following extension to ``conf.py`` in the documentation directory:

::

    extensions = [
        ...
        "django_setup_configuration.documentation.setup_config_example",
        ...
    ]

And then display a YAML example by using the directive:

::

    .. setup-config-example:: path.to.your.ConfigurationStep

which will produce something like the following example (in the case of the ``SitesConfigurationStep`` provided by this library):

.. setup-config-example:: django_setup_configuration.contrib.sites.steps.SitesConfigurationStep

.. warning::

    Not all possible configurations are supported by this directive currently.
    More complex type annotations like ``list[ComplexObject | ComplexObject]`` will raise errors when
    trying to build the documentation
