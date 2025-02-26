# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'netLD / ThirdEye SDK'
copyright = '2025, LogicVein'
author = 'LogicVein'

release = 'r20241218.0941'
version = 'r20241218.0941'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']

html_css_files = [
    'css/theme_overrides.css',
]

# -- Options for EPUB output
epub_show_urls = 'footnote'
