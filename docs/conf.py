# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import sys
sys.path.insert(0, 'C:\\Users\\LUGGGI\\OneDrive - bwedu\\Vorlesungen\\Bachlor_Arbeit\\Code\\SPS_Software')

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'MiniFactory'
copyright = '2023, Lukas Beck'
author = 'Lukas Beck'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.napoleon', 
    'sphinx_markdown_builder'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'en'

# -- Autodoc configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

autodoc_default_options = {
    'member-order': 'bysource',
    'undoc-members': False,
    'private-members': False,
    'exclude-members': 'Attributes',
    'special-members': '__init__'
}

# Napoleon
napoleon_include_private_with_doc = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
# html_static_path = ['_static']
html_theme_options = {
    "sidebarwidth": "20%",
    "fixed_sidebar": False,
}

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration

todo_include_todos = True
