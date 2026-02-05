# Sphinx Documentation Configuration

## Overview

This directory will contain the Sphinx API documentation for the Pipe Network Simulation Application.

## Setup Instructions

### 1. Install Sphinx

```bash
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
```

### 2. Initialize Sphinx

```bash
cd docs
sphinx-quickstart
```

When prompted:
- Separate source and build directories: **Yes**
- Project name: **Pipe Network Simulation**
- Author name: **Your Name**
- Project version: **1.0**
- Project language: **en**

### 3. Configure conf.py

Edit `docs/source/conf.py`:

```python
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
]

html_theme = 'sphinx_rtd_theme'

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'special-members': '__init__',
    'inherited-members': True,
    'show-inheritance': True,
}
```

### 4. Create index.rst

```rst
Welcome to Pipe Network Simulation Documentation
=================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/models
   modules/services
   modules/map
   modules/ui
   modules/controllers

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
```

### 5. Generate API Documentation

```bash
cd docs
sphinx-apidoc -o source/modules ../app
```

### 6. Build Documentation

```bash
make html  # Linux/Mac
.\make.bat html  # Windows
```

### 7. View Documentation

Open `docs/build/html/index.html` in a web browser.

## Documentation Structure

```
docs/
├── source/
│   ├── conf.py           # Sphinx configuration
│   ├── index.rst         # Main documentation page
│   └── modules/          # Auto-generated module docs
│       ├── models.rst
│       ├── services.rst
│       ├── map.rst
│       ├── ui.rst
│       └── controllers.rst
├── build/
│   └── html/             # Generated HTML documentation
└── README_SPHINX.md      # This file
```

## Writing Docstrings

Use Google-style docstrings:

```python
def calculate_pressure_drop(pipe: Pipe, fluid: Fluid) -> float:
    """Calculate pressure drop in a pipe.
    
    Uses the Darcy-Weisbach equation with Colebrook-White
    friction factor calculation.
    
    Args:
        pipe: Pipe object with geometry and flow properties
        fluid: Fluid object with density and viscosity
        
    Returns:
        Pressure drop in Pa
        
    Raises:
        ValueError: If pipe diameter or flow rate is invalid
        
    Example:
        >>> pipe = Pipe(id="P1", diameter=0.1, length=100)
        >>> fluid = Fluid(density=998.0, viscosity=1e-3)
        >>> dp = calculate_pressure_drop(pipe, fluid)
        >>> print(f"Pressure drop: {dp:.2f} Pa")
    """
    # Implementation
```

## Continuous Documentation

To rebuild docs automatically during development:

```bash
pip install sphinx-autobuild
sphinx-autobuild source build/html
```

Then open http://127.0.0.1:8000 in a browser.

## Publishing

### GitHub Pages

1. Build documentation: `make html`
2. Copy `build/html/*` to `docs/` directory
3. Enable GitHub Pages in repository settings
4. Point to `docs/` folder

### Read the Docs

1. Create account at readthedocs.org
2. Import project from GitHub
3. Documentation builds automatically on commits

## Additional Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
- [Napoleon Extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
