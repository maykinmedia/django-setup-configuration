{% block link %}{{ link }}{% endblock %}

{% block title %}{{ title }}{% endblock %}

Settings Overview
=================

Enable/Disable configuration:
"""""""""""""""""""""""""""""

{% if required_settings %}
::

    {% spaceless %}
    {{ enable_settings }}
    {% endspaceless %}
{% endif %}

{% if required_settings %}
Required:
"""""""""

::

    {% spaceless %}
    {% for setting in required_settings %}{{ setting }}
    {% endfor %}
    {% endspaceless %}
{% endif %}

All settings:
"""""""""""""

::

    {% spaceless %}
    {% for setting in all_settings %}{{ setting }}
    {% endfor %}
    {% endspaceless %}

Detailed Information
====================

::

    {% spaceless %}
    {% for detail in detailed_info %}
    {% for part in detail %}{{ part|safe }}
    {% endfor %}{% endfor %}
    {% endspaceless %}
