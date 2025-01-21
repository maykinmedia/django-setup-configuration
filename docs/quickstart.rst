==========
Quickstart
==========

Installation
============

The package can be installed from PyPI using pip:

.. code-block:: bash

    pip install django-setup-configuration

Configuration
=============

See :ref:`config_docs`.


.. _usage_docs:

Command usage
=============

.. autoproperty:: django_setup_configuration.management.commands.setup_configuration.Command.help

To automatically configure your application, this library provides the
command line tool ``setup_configuration`` to assist with this configuration by loading a
YAML file in which the configuration information is specified.

.. code-block:: bash

    src/manage.py setup_configuration --yaml-file /path/to/your/yaml

You can get the full command documentation with:

.. code-block:: bash

    src/manage.py setup_configuration --help

.. warning:: This command is declarative - each step is idempotent,
    so it's safe to run the command multiple times. The steps will overwrite any
    manual changes made in the admin if you run the command after making these changes.

The command accepts a **single** YAML file that contains configuration in a separate namespace for
each configuration step the application provides. Individual steps can be enabled or disabled by
setting the corresponding ``_enable`` flag to ``true`` or ``false``.

This YAML file could look something like this:

.. code-block:: yaml

    sites_config_enable: true
    sites_config:
      items:
      - domain: example.com
        name: Example site
      - domain: test.example.com
        name: Test site
    other_config_enable: false
    other_config:
      items:
      - ...

You can validate your config file, without actually executing any of the steps, by using the the ``validate-only`` flag:

.. code-block:: bash

    src/manage.py setup_configuration --yaml-file /path/to/your/yaml --validate-only

The command will report any validation errors on raise a non-zero exit code if the yaml file cannot be loaded.
Note that this check only verifies that the yaml file is well-formed, i.e. that it has the required shape and that all
values are of the correct type. Whether or not the values are correct will only be known when actually executing the steps.

Integrating with deployment
---------------------------

One way of integrating ``setup_configuration`` into your deployment is by adding an extra container
that runs a script that executes the ``setup_configuration`` command. This container requires
a volume to mount the YAML file.

.. code-block:: yaml

    web-setup-config:
      image: <docker-image>
      environment: *web_env
      command: /setup_configuration.sh
      volumes:
      - ./path/to/config.yaml:/app/config.yaml
      - ./path/to/setup_configuration.sh:/setup_configuration.sh
      depends_on:
      - db
      - redis

Example of ``setup_configuration.sh``:

.. code-block:: shell

    #!/bin/bash

    # setup initial configuration using environment variables
    # Run this script from the root of the repository

    set -e

    # Figure out abspath of this script
    SCRIPT=$(readlink -f "$0")
    SCRIPTPATH=$(dirname "$SCRIPT")

    # wait for required services
    ${SCRIPTPATH}/wait_for_db.sh

    src/manage.py migrate
    src/manage.py setup_configuration --yaml-file config.yaml
