=========
Changelog
=========

0.4.0 (2024-11-28)
==================

💥 **NOTE**: This release contains a number of significantly breaking changes. 💥

* The core API of the configuration steps has been changed to rely on Pydantic-based
  configuration models, and to rely solely on an ``execute`` hook, with ``is_configured``
  and ``test_results`` being deprecated. Details of the new API can be found in the
  README.
* The ``generate_config_docs`` command has been disabled until it can amended to work
  with the new API, which is planned for an upcoming release.

0.3.0 (2024-07-15)
==================

* added option ``--dry-run`` for ``generate_config_docs`` management command to check that docs are
  up-to-date without creating them.

0.2.0 (2024-07-11)
==================

* ``generate_config_docs`` management command added to autogenerate documentation based on configurationsteps

0.1.0 (2024-03-21)
==================

First release. Features:

* ``setup_configuration`` management command
* ``BaseConfigurationStep`` base class.
