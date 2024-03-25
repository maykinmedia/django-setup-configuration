

Welcome to django_setup_configuration's documentation!
======================================================

:Version: 0.1.0
:Source: https://github.com/maykinmedia/django-setup-configuration
:Keywords: Configuration
:PythonVersion: 3.10

|build-status| |code-quality| |black| |coverage| |docs|

|python-versions| |django-versions| |pypi-version|

Manage your configuration via django command.

.. contents::

.. section-numbering::

Features
========

* management command, which runs the ordered list of all configuration steps

Installation
============

Requirements
------------

* Python 3.10 or above
* Django 3.2 or newer


Install
-------

1. Install from PyPI

.. code-block:: bash

    pip install django-setup-configuration

2. Add ``django_setup_configuration`` to the ``INSTALLED_APPS`` setting.


Usage
=====

1. Create configurations steps based on ``BaseConfigurationStep`` class.

2. Specify these steps in ``SETUP_CONFIGURATION_STEPS`` setting.

3. Run ``setup_configuration`` management command manually or put it in the init container
   during deployment.


Local development
=================

To install and develop the library locally, use:

.. code-block:: bash

    pip install -e .[tests,coverage,docs,release]

When running management commands via ``django-admin``, make sure to add the root
directory to the python path (or use ``python -m django <command>``):

.. code-block:: bash

    export PYTHONPATH=. DJANGO_SETTINGS_MODULE=testapp.settings
    django-admin check
    # or other commands like:
    # django-admin makemessages -l nl


.. |build-status| image:: https://github.com/maykinmedia/django_setup_configuration/workflows/Run%20CI/badge.svg
    :alt: Build status
    :target: https://github.com/maykinmedia/django_setup_configuration/actions?query=workflow%3A%22Run+CI%22

.. |code-quality| image:: https://github.com/maykinmedia/django_setup_configuration/workflows/Code%20quality%20checks/badge.svg
     :alt: Code quality checks
     :target: https://github.com/maykinmedia/django_setup_configuration/actions?query=workflow%3A%22Code+quality+checks%22

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |coverage| image:: https://codecov.io/gh/maykinmedia/django_setup_configuration/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/maykinmedia/django_setup_configuration
    :alt: Coverage status

.. |docs| image:: https://readthedocs.org/projects/django_setup_configuration/badge/?version=latest
    :target: https://django_setup_configuration.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/django_setup_configuration.svg

.. |django-versions| image:: https://img.shields.io/pypi/djversions/django_setup_configuration.svg

.. |pypi-version| image:: https://img.shields.io/pypi/v/django_setup_configuration.svg
    :target: https://pypi.org/project/django_setup_configuration/
