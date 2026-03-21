project = "The Judgemental Monad"
author = "Teague Sterling"
copyright = "2025-2026, Teague Sterling"

extensions = [
    "myst_parser",
]

myst_enable_extensions = [
    "colon_fence",
    "fieldlist",
    "dollarmath",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", ".git", ".venv", "README.md", "drafts", "experiments", "docs"]

# -- Furo theme ---------------------------------------------------------------

html_theme = "furo"

# Ink and amber — warm, dark, contemplative.
# The writing is about 間 (ma). The theme should have it.
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#6e4b3a",       # warm ink
        "color-brand-content": "#4a3728",        # deep umber for links
        "color-admonition-background": "#faf6f1", # parchment tint
    },
    "dark_css_variables": {
        "color-brand-primary": "#d4a574",        # amber
        "color-brand-content": "#c9956b",        # warm gold for links
        "color-background-primary": "#1a1612",   # near-black with warmth
        "color-background-secondary": "#221e19", # sidebar, slightly lighter
        "color-admonition-background": "#2a2420", # warm dark boxes
    },
    "light_logo": "logo-light.svg",
    "dark_logo": "logo-dark.svg",
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}

html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Clean presentation — no clutter
html_title = "The Judgemental Monad"
html_show_sourcelink = False

# Suppress "document isn't included in any toctree" warnings for linked pages
# Temporarily show all warnings during restructure verification
# suppress_warnings = ["myst.xref_missing"]
