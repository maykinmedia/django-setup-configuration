===========================================
``django.contrib.sites.Site`` configuration
===========================================

This library provides a ``ConfigurationStep`` for the ``django.contrib.sites.Site`` model.
To make use of this, add the step to your ``SETUP_CONFIGURATION_STEPS``:

.. code-block:: python

    SETUP_CONFIGURATION_STEPS = [
        ...
        "django_setup_configuration.contrib.sites.steps.SitesConfigurationStep",
        ...
    ]

Create or update your YAML configuration file with your settings:

.. code-block:: yaml

    sites_config_enable: true
    sites_config:
      items:
      - domain: example.com
        name: Example site
      - domain: test.example.com
        name: Test site

.. note::
    The first item in the list will be used to update the current ``Site`` instance,
    the rest will be added or updated (if a ``Site`` already exists for that ``domain``).
