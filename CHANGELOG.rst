=========
Changelog
=========

0.8.1 (2025-05-12)
==================

**Bugfixes**

* [#71] The fix for incorrect annotations for the default value in blank fields,
  introduced in 0.8.0, was not properly fixed for unmapped Django field types. This
  release addresses the issue so that the default type is properly accounted for also
  for unmapped field types.

0.8.0 (2025-05-08)
==================

**Bugfixes**

* [#68] Fix an issue whereby the annotation for Django fields would be incorrectly
  generated and raise an exception when ``blank=True`` and ``default=bool|None``.
  Defaults will now always be validated according to the field's base annotation, which
  will be expanded if necessary to accommodate the default.

0.7.2 (2025-03-24)
==================

**Maintenance**

* [#open-zaak/open-zaak#1856] Allow Django 5 as a dependency.

0.7.1 (2025-02-10)
==================

**Bugfixes**

* [#62] Fix ``setup-config-usage`` ToS step links

0.7.0 (2025-02-06)
==================

**New features**

* Add a directive for general purpose documentation in downstream projects

**Bugfixes and QoL Changes**

* Do not mark blank=True strings as polymorphic
* [#58] Add example for UUID field in directive
* Provide more descriptive errors on step loading in runner

0.6.0 (2025-01-23)
==================

**New features**

* Add a ``validate-only`` flag to support web-init/CI usage
* [#45] Sphinx directive to generate YAML examples for config models

**Bugfixes and QoL changes**

* [#31] Bypass validation of defaults for Django fields containing choices
* [#39] Make command output clearer and less opaque
* [#29] Accept Path objects for YAML files
* [#42] Handle Site creation in SitesConfigurationStep when no Sites models
* [#37] Explicitly handle transactions in the runner

**Documentation**

* [#49] Add documentation for ``setup_configuration`` command usage

0.5.0 (2024-12-13)
==================

* Fixed an issue (#27) whereby empty strings would not be part of the string literal
  inferred from a string-based field's ``options`` when using a Django field ref.
* Added a generic configuration step for the Django sites module.
* Slug fields are now explicitly validated in Django field refs.

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
