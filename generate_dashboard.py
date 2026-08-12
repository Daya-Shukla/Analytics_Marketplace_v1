#!/usr/bin/env python3
"""
generate_dashboard.py
======================

Minimal example driver script. Running this with no arguments builds
the dashboard using entirely default settings (the built-in synthetic
sample catalog and the default Microsoft-style theme) - a quick way to
sanity-check the package is installed correctly.

Usage
-----
    python generate_dashboard.py
    python generate_dashboard.py --config config.example.json --reports reports.example.json --output out.html

This is a thin wrapper around ``tech_marketplace.cli.main`` - see
``tech_marketplace/cli.py`` for the full flag reference, or run
``python generate_dashboard.py --help``.
"""

import sys

from tech_marketplace.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
