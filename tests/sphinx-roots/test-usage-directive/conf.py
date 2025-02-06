# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Test Project"
copyright = "2000-2042, The Test Project Authors"
author = "The Authors"
version = release = "4.16"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.intersphinx",
    "django_setup_configuration.documentation.setup_config_example",
    "django_setup_configuration.documentation.setup_config_usage",
]
