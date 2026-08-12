"""
renderer.py
============

Glues everything together: takes an ``AppConfig`` and a list of
``Report`` objects, feeds them into the Jinja2 template in
``templates/marketplace.html.j2``, and writes out a single,
self-contained HTML file (no external CSS/JS files, no build step,
no server - just open it in a browser).

Typical usage
-------------
    from tech_marketplace import AppConfig, load_reports, MarketplaceRenderer

    config = AppConfig.from_overrides({"theme": {"brand": "#8764b8"}})
    reports = load_reports("my_reports.json", base_url=config.section("data")["base_url"])
    MarketplaceRenderer(config, reports).build("dashboard.html")

Or, for the common case of "just use the defaults / a config file",
use the :func:`build_dashboard` convenience function instead of
wiring the pieces together by hand.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import AppConfig, DEFAULT_CONFIG, deep_merge
from .data_source import Report, load_reports, reports_to_json

TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_NAME = "marketplace.html.j2"


def load_config_file(path: Optional[str]) -> Dict[str, Any]:
    """
    Load a user config override file (JSON) and return it as a plain
    dict, ready to pass to ``AppConfig.from_overrides``.

    Returns an empty dict (i.e. "use built-in defaults untouched") when
    ``path`` is ``None``. Only the keys present in the file need to be
    specified - see :func:`~tech_marketplace.models.deep_merge`.
    """
    if not path:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class MarketplaceRenderer:
    """
    Renders the marketplace HTML page from a config + report catalog.

    Parameters
    ----------
    config: An ``AppConfig`` instance (or a plain dict, which will be
        merged onto the defaults automatically).
    reports: The list of ``Report`` objects to display.
    """

    def __init__(self, config: AppConfig | Dict[str, Any], reports: List[Report]):
        if isinstance(config, AppConfig):
            self.config = config
        else:
            self.config = AppConfig.from_overrides(config)
        self.reports = reports

        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(disabled_extensions=(".j2",), default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # -- context building -------------------------------------------------

    def _build_context(self) -> Dict[str, Any]:
        """
        Assemble the full Jinja2 template context.

        Most values are simply the matching ``AppConfig`` section
        (``branding``, ``theme``, ``icons``, ``search``, ``labels``)
        passed straight through so the template can use dot access
        (e.g. ``{{ branding.hero_title }}``). A few values are
        pre-serialized to JSON here (``reports_json``, ``prompts_json``,
        ``labels_json``, ``icons_json``, ``data_config_json``) so the
        `<script>` block in the template can drop them straight into
        JavaScript ``const`` declarations without needing Jinja's
        ``tojson`` filter sprinkled through the script.
        """
        cfg = self.config.as_dict()
        return {
            "branding": cfg["branding"],
            "theme": cfg["theme"],
            "theme_css": self.config.css_variables(),
            "icons": cfg["icons"],
            "search": cfg["search"],
            "labels": cfg["labels"],
            "reports_json": reports_to_json(self.reports),
            "prompts_json": json.dumps(cfg["search"]["prompts"]),
            "labels_json": json.dumps(cfg["labels"]),
            "icons_json": json.dumps(cfg["icons"]),
            "data_config_json": json.dumps(cfg["data"]),
        }

    # -- rendering ----------------------------------------------------------

    def render(self) -> str:
        """Render and return the full HTML document as a string."""
        template = self._env.get_template(TEMPLATE_NAME)
        return template.render(**self._build_context())

    def build(self, output_path: Optional[str] = None) -> Path:
        """
        Render the page and write it to ``output_path`` (falling back to
        ``AppConfig.data.output`` / ``"technology_analytics_marketplace_dashboard.html"``
        if not given). Creates parent directories as needed. Returns the
        ``Path`` written to.
        """
        html = self.render()
        target = Path(
            output_path
            or self.config.section("data").get("output_path")
            or "technology_analytics_marketplace_dashboard.html"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        return target


def build_dashboard(
    config_path: Optional[str] = None,
    reports_path: Optional[str] = None,
    output_path: Optional[str] = None,
    config_overrides: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    One-call convenience wrapper for the common case.

    Parameters
    ----------
    config_path: Optional path to a JSON file of ``AppConfig`` overrides.
    reports_path: Optional path to a JSON/CSV file of reports. Falls
        back to the built-in synthetic sample catalog when omitted.
    output_path: Where to write the generated HTML file.
    config_overrides: Optional dict of additional config overrides,
        applied on top of anything loaded from ``config_path`` (useful
        for scripting one-off tweaks without writing a file).

    Returns
    -------
    pathlib.Path to the file that was written.
    """
    file_overrides = load_config_file(config_path)
    overrides = deep_merge(file_overrides, config_overrides or {})
    config = AppConfig.from_overrides(overrides)

    data_section = config.section("data")
    reports_source = reports_path or data_section.get("reports_source")
    reports = load_reports(reports_source, base_url=data_section.get("base_url", ""))

    return MarketplaceRenderer(config, reports).build(output_path)
