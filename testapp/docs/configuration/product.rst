.. _product:

=====================
Product Configuration
=====================

Settings Overview
=================

Enable/Disable configuration:
"""""""""""""""""""""""""""""

::

    PRODUCT_CONFIG_ENABLE

Required:
"""""""""

::

    PRODUCT_NAME
    PRODUCT_SERVICE_URL

All settings:
"""""""""""""

::

    PRODUCT_NAME
    PRODUCT_SERVICE_URL
    PRODUCT_TAGS

Detailed Information
====================

::

    Variable            PRODUCT_NAME
    Setting             Name
    Description         The name of the product
    Possible values     string
    Default value       No default
    
    Variable            PRODUCT_SERVICE_URL
    Setting             Service url
    Description         The url of the service
    Possible values     string (URL)
    Default value       No default
    
    Variable            PRODUCT_TAGS
    Setting             tags
    Description         Tags for the product
    Possible values     string, comma-delimited ('foo,bar,baz')
    Default value       example_tag
