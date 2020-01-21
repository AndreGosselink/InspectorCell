# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import sys
import shutil
import warnings
import subprocess
from pathlib import Path

# add project source
root = Path(__file__).absolute().parents[2]
packages = root / 'src'
sys.path.insert(0, str(packages))

# copy destlog into the documentation source
shutil.copyfile(
    str(root / 'CHANGELOG.rst'),
    str(root / 'doc' / 'source' / 'changelog.rst')
    )

from inspectorcell import __version__
# warnings.warn('Could not import repository')

rst_epilog = """
.. |LatestWheel| replace:: :download:`0.2.2 </_static/dist/inspectorcell-0.2.2-py3-none-any.whl>`
"""

# build the filelist
# rst_epilog = """
# .. |WhlList| replace:: {}
# """
# whllist = []
# distp = Path(__file__).parent /'_static' / 'dist'
# entry = ':download:`{} </_static/dist/{}>`'
# for whl in distp.glob('*.whl'):
#     ver = whl.name.split('+')
#     if len(ver) == 1:
#         ver, = ver
#     else:
#         gver, lver = ver
#         ver = gver + '+' +lver.split('.')[0]
# 
#     whllist.append(entry.format(ver, whl.name))
# rst_epilog = rst_epilog.format(', '.join(whllist))

# -- Project information -----------------------------------------------------

project = 'InspectorCell'
copyright = '2019, InspectorCell'
author = 'Tatsiana Hofer and Andre Gosselink'
release = __version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
]

# setup for autodoc
autodoc_default_options = {
    'members': True,
    'member-order': 'groupwise',
    'no-undoc-members': True,
    'undoc-members': False,
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
