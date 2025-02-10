# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import sys
from pathlib import Path

import django
from django.conf import settings

current_dir = Path(__file__).parents[1]
code_directory = current_dir / "django_setup_configuration"

sys.path.insert(0, str(code_directory))


# Mock the Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mock_settings")

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.sites",  # Required by Django models
        ],
    )

django.setup()


# -- Project information -----------------------------------------------------

project = "django_setup_configuration"
copyright = "2024, Maykin Media"
author = "Maykin Media"

# The full version, including alpha/beta/rc tags
release = "0.7.1"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "django_setup_configuration.documentation.setup_config_example",
    "django_setup_configuration.documentation.setup_config_usage",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []
