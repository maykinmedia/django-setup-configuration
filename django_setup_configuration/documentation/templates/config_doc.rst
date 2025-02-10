You can use the included ``setup_configuration`` management command to configure your
instance from a yaml file as follows:

.. code-block:: bash

    python manage.py setup_configuration --yaml-file /path/to/config.yaml

You can also validate that the configuration source can be successfully loaded,
without actually running the steps, by adding the ``validate-only`` flag:

.. code-block:: bash

    python manage.py setup_configuration --yaml-file /path/to/config.yaml --validate-only

Both commands will either return 0 and a success message if the configuration file can
be loaded without issues, otherwise it will return a non-zero exit code and print any
validation errors.

Your YAML file should contain both a flag indicating whether the step is enabled or
disabled, as well as an object containing the actual configuration values under the
appropriate key.

.. note:: All steps are disabled by default. You only have to explicitly include the
            flag to enable a step, not to disable it, though you may do so if you wish to
            have an explicit record of what steps are disabled.

Further information can be found at the `django-setup-configuration
<https://django-setup-configuration.readthedocs.io/en/{{ package_version }}/quickstart.html#command-usage>`_ documentation.

{% if show_toc %}

{% if show_steps %}
This projects includes the following configuration steps (click on each step for a
brief descripion and an example YAML you can include in your config file):
{% else %}
This projects includes the following configuration steps:
{% endif %}

{% for step in steps %}
- {% if show_steps %}`{{ step.title }} <#{{ step.module_path }}>`_{% else %} {{ step.title }} {% endif %}
{% endfor %}
{% endif %}
