"""
data_source.py
===============

Everything related to *where the catalog of reports comes from*.

Ships with an 8-item synthetic sample catalog (a straight port of the
original hand-written page's data) so the generator works out of the
box with zero configuration. For real use, point ``load_reports`` at
a JSON or CSV file - or bypass files entirely and pass a list of
dicts/``Report`` objects straight from whatever system owns the real
catalog (a Power BI REST API pull, a SharePoint list export, an
internal metadata service, etc).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Union

from .models import Report

# ---------------------------------------------------------------------------
# Built-in sample catalog
# ---------------------------------------------------------------------------

#: Synthetic sample reports, used whenever no external data source is
#: configured. Replace this with a real feed in production - see the
#: module docstring for common sources. Keys use the same shape
#: ``Report.from_dict`` expects, so this list can be dropped straight
#: into a JSON file to use as a starting point for a real catalog.
DEFAULT_REPORTS: List[Dict[str, Any]] = [
    {
        "id": "app-health",
        "name": "Application Health Dashboard",
        "domain": "Operations",
        "owner": "Application Operations",
        "contact": "AppOps Team",
        "platform": "Power BI",
        "last_refresh": "5 minutes ago",
        "views": 1842,
        "rating": 4.9,
        "accent": "#0f6cbd",
        "description": "Availability, uptime, latency, response time, error rate and service health across critical applications.",
        "keywords": ["application", "health", "uptime", "availability", "latency", "outage", "error", "monitoring", "sla"],
        "tags": ["Application", "Health", "Availability", "SLA"],
        "url": "https://contoso.example/reports/application-health",
    },
    {
        "id": "cloud-cost",
        "name": "Cloud Cost Optimization",
        "domain": "Cloud",
        "owner": "FinOps",
        "contact": "Cloud FinOps Team",
        "platform": "Power BI",
        "last_refresh": "15 minutes ago",
        "views": 2215,
        "rating": 4.8,
        "accent": "#0078d4",
        "description": "Cloud spend, utilization, forecast, rightsizing, reserved capacity and savings opportunities.",
        "keywords": ["cloud", "cost", "spend", "azure", "forecast", "finops", "savings", "utilization", "rightsizing"],
        "tags": ["Cloud", "Cost", "FinOps", "Optimization"],
        "url": "https://contoso.example/reports/cloud-cost-optimization",
    },
    {
        "id": "security-risk",
        "name": "Cyber Security Risk Dashboard",
        "domain": "Security",
        "owner": "Cyber Defense",
        "contact": "Cyber Risk Team",
        "platform": "Power BI",
        "last_refresh": "30 minutes ago",
        "views": 1764,
        "rating": 4.7,
        "accent": "#d13438",
        "description": "Vulnerability exposure, remediation progress, risk aging, policy exceptions and cyber posture trends.",
        "keywords": ["cyber", "security", "risk", "vulnerability", "threat", "remediation", "patch", "control", "posture"],
        "tags": ["Security", "Risk", "Vulnerability", "Controls"],
        "url": "https://contoso.example/reports/cyber-security-risk",
    },
    {
        "id": "portfolio",
        "name": "Technology Portfolio Dashboard",
        "domain": "Architecture",
        "owner": "Enterprise Architecture",
        "contact": "Architecture Office",
        "platform": "Power BI",
        "last_refresh": "1 hour ago",
        "views": 1312,
        "rating": 4.6,
        "accent": "#107c10",
        "description": "Application inventory, ownership, lifecycle, technology currency, modernization and investment alignment.",
        "keywords": ["portfolio", "application", "inventory", "lifecycle", "modernization", "ownership", "architecture", "technology currency"],
        "tags": ["Portfolio", "Architecture", "Modernization", "Lifecycle"],
        "url": "https://contoso.example/reports/technology-portfolio",
    },
    {
        "id": "incident-command",
        "name": "Incident Command Center",
        "domain": "Service Management",
        "owner": "Technology Operations",
        "contact": "Service Management Office",
        "platform": "Power BI",
        "last_refresh": "10 minutes ago",
        "views": 2488,
        "rating": 4.9,
        "accent": "#f7630c",
        "description": "Major incidents, open incidents, MTTR, SLA compliance, severity trends and service restoration metrics.",
        "keywords": ["incident", "outage", "mttr", "sla", "severity", "service", "ticket", "downtime", "production"],
        "tags": ["Incident", "Service", "MTTR", "SLA"],
        "url": "https://contoso.example/reports/incident-command-center",
    },
    {
        "id": "devops-metrics",
        "name": "DevOps Delivery Metrics",
        "domain": "Engineering",
        "owner": "Engineering Excellence",
        "contact": "DevOps Enablement",
        "platform": "Power BI",
        "last_refresh": "45 minutes ago",
        "views": 1198,
        "rating": 4.5,
        "accent": "#5c2d91",
        "description": "Deployment frequency, lead time, change failure rate, release flow and engineering throughput.",
        "keywords": ["devops", "deployment", "release", "pipeline", "lead time", "change failure", "engineering", "delivery"],
        "tags": ["DevOps", "Engineering", "Release", "Delivery"],
        "url": "https://contoso.example/reports/devops-delivery",
    },
    {
        "id": "data-platform",
        "name": "Data Platform Health",
        "domain": "Data",
        "owner": "Data Platform",
        "contact": "Data Engineering Team",
        "platform": "Power BI",
        "last_refresh": "20 minutes ago",
        "views": 1034,
        "rating": 4.4,
        "accent": "#0099bc",
        "description": "Pipeline health, data quality, job failures, SLA adherence, freshness and platform stability.",
        "keywords": ["data", "pipeline", "quality", "freshness", "platform", "etl", "failure", "sla", "engineering"],
        "tags": ["Data", "Pipeline", "Quality", "Freshness"],
        "url": "https://contoso.example/reports/data-platform-health",
    },
    {
        "id": "capacity",
        "name": "Infrastructure Capacity Dashboard",
        "domain": "Infrastructure",
        "owner": "Infrastructure Engineering",
        "contact": "Infrastructure Capacity Team",
        "platform": "Power BI",
        "last_refresh": "2 hours ago",
        "views": 912,
        "rating": 4.3,
        "accent": "#8764b8",
        "description": "Compute, storage, network utilization, capacity forecast, saturation and infrastructure demand trends.",
        "keywords": ["infrastructure", "capacity", "server", "storage", "network", "utilization", "forecast", "compute"],
        "tags": ["Infrastructure", "Capacity", "Forecast", "Utilization"],
        "url": "https://contoso.example/reports/infrastructure-capacity",
    },
]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

ReportsInput = Union[None, str, Path, Sequence[Union[Dict[str, Any], Report]]]


def _read_json_file(path: Path) -> List[Dict[str, Any]]:
    """Read a JSON file containing a list of report objects."""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and "reports" in payload:
        # Allow either a bare list or {"reports": [...]}
        payload = payload["reports"]
    if not isinstance(payload, list):
        raise ValueError(f"{path}: expected a JSON list of reports (or a {{'reports': [...]}} object).")
    return payload


def _read_csv_file(path: Path) -> List[Dict[str, Any]]:
    """
    Read a CSV file of reports.

    ``keywords`` and ``tags`` columns are treated as pipe-delimited
    (``cloud|cost|finops``) since CSV has no native list type.
    """
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            row: Dict[str, Any] = dict(raw_row)
            for list_field in ("keywords", "tags"):
                if row.get(list_field):
                    row[list_field] = [item.strip() for item in row[list_field].split("|") if item.strip()]
                else:
                    row[list_field] = []
            for numeric_field, caster in (("views", int), ("rating", float)):
                if row.get(numeric_field) not in (None, ""):
                    row[numeric_field] = caster(row[numeric_field])
            rows.append(row)
    return rows


def load_reports(source: ReportsInput = None, base_url: str = "") -> List[Report]:
    """
    Load and normalize a catalog of reports into ``Report`` objects.

    Parameters
    ----------
    source:
        One of:

        * ``None`` - use :data:`DEFAULT_REPORTS` (the built-in sample catalog).
        * a path (``str``/``pathlib.Path``) to a ``.json`` or ``.csv`` file.
        * a list already in memory, containing dicts and/or ``Report`` instances
          (useful when the catalog comes from an API call or a database query
          rather than a file).
    base_url:
        Passed through so relative report URLs can be resolved eagerly;
        see :meth:`Report.resolved_url`. Pass ``""`` to leave URLs as-is.

    Returns
    -------
    List[Report]
    """
    if source is None:
        raw_items: List[Dict[str, Any]] = DEFAULT_REPORTS
    elif isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Reports source not found: {path}")
        if path.suffix.lower() == ".json":
            raw_items = _read_json_file(path)
        elif path.suffix.lower() == ".csv":
            raw_items = _read_csv_file(path)
        else:
            raise ValueError(f"Unsupported reports file type: {path.suffix} (use .json or .csv)")
    else:
        # Already an in-memory sequence of dicts/Report objects.
        raw_items = list(source)  # type: ignore[arg-type]

    reports: List[Report] = []
    for item in raw_items:
        report = item if isinstance(item, Report) else Report.from_dict(item)
        if base_url:
            report.url = report.resolved_url(base_url)
        reports.append(report)
    return reports


def reports_to_json(reports: List[Report]) -> str:
    """Serialize a list of ``Report`` objects to a JSON array string, for embedding in the page."""
    return json.dumps([r.to_dict() for r in reports], indent=2)
