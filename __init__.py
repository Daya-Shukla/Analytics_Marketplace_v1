"""
cli.py
======

Command-line entry point for generating the dashboard without writing
any Python. Run as a module:

    python -m tech_marketplace --output dashboard.html

or, with full customization:

    python -m tech_marketplace \\
        --config my_config.json \\
        --reports my_reports.json \\
        --output dashboard.html
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .renderer import build_dashboard


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser (split out from main() so it's testable/importable)."""
    parser = argparse.ArgumentParser(
        prog="tech_marketplace",
        description=(
            "Generate the Technology Analytics Marketplace dashboard as a "
            "single, self-contained HTML file."
        ),
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to a JSON file of AppConfig overrides (branding, theme, icons, labels, ...). "
             "Only the keys you want to change need to be present - see config.example.json.",
    )
    parser.add_argument(
        "--reports",
        metavar="PATH",
        help="Path to a JSON or CSV file of reports to catalog. Defaults to the built-in "
             "synthetic sample catalog - see reports.example.json for the expected shape.",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        default="technology_analytics_marketplace_dashboard.html",
        help="Where to write the generated HTML file (default: %(default)s).",
    )
    parser.add_argument(
        "--base-url",
        metavar="URL",
        help="Prefix applied to any relative report URL (overrides data.base_url in --config).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    overrides = {}
    if args.base_url:
        overrides["data"] = {"base_url": args.base_url}

    try:
        output_path = build_dashboard(
            config_path=args.config,
            reports_path=args.reports,
            output_path=args.output,
            config_overrides=overrides,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    resolved = Path(output_path).resolve()
    print(f"Dashboard written to: {resolved}")
    print(f"Open it directly in a browser, e.g.: file://{resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
