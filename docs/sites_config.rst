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

Create or update your YAML configuration file with syour settings:

.. pydantic-model-example:: django_setup_configuration.contrib.sites.steps.SitesConfigurationStep

.. note::
    The first item in the list will be used to update the current ``Site`` instance,
    the rest will be added or updated (if a ``Site`` already exists for that ``domain``).
