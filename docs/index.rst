.. django_setup_configuration documentation master file, created by startproject.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django_setup_configuration's documentation!
======================================================

|build-status| |code-quality| |black| |coverage|

..
   |docs| |python-versions| |django-versions| |pypi-version|

Django Setup Configuration allows to make a pluggable configuration setup
used with the django management command.

Features
========

* management command, which runs the ordered list of all configuration steps

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart.rst

   config_docs.rst

`Quickstart <./quickstart.rst>`_

`Configuration docs <./config_docs.rst>`_



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. |build-status| image:: https://github.com/maykinmedia/django-setup-configuration/workflows/Run%20CI/badge.svg
    :alt: Build status
    :target: https://github.com/maykinmedia/django-setup-configuration/actions?query=workflow%3A%22Run+CI%22

.. |code-quality| image:: https://github.com/maykinmedia/django-setup-configuration/workflows/Code%20quality%20checks/badge.svg
     :alt: Code quality checks
     :target: https://github.com/maykinmedia/django-setup-configuration/actions?query=workflow%3A%22Code+quality+checks%22

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |coverage| image:: https://codecov.io/gh/maykinmedia/django-setup-configuration/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/maykinmedia/django-setup-configuration
    :alt: Coverage status

..
   .. |docs| image:: https://readthedocs.org/projects/django_setup_configuration/badge/?version=latest
       :target: https://django_setup_configuration.readthedocs.io/en/latest/?badge=latest
       :alt: Documentation Status

   .. |python-versions| image:: https://img.shields.io/pypi/pyversions/django-setup-configuration.svg

   .. |django-versions| image:: https://img.shields.io/pypi/djversions/django-setup-configuration.svg

   .. |pypi-version| image:: https://img.shields.io/pypi/v/django-setup-configuration.svg
       :target: https://pypi.org/project/django-setup-configuration/
