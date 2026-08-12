# Technology Analytics Marketplace (Python generator)

A Python package that generates the **Technology Analytics
Marketplace** self-service report/dashboard catalog as a single,
polished, offline-friendly HTML file — a search-and-filter landing
page for finding the right BI report or dashboard without knowing
where it lives.

This is a Python-generated rebuild of a hand-written HTML prototype.
Instead of one big file mixing markup, styling, data and behavior, it
splits into:

| Piece | File | What it controls |
|---|---|---|
| Data model | `tech_marketplace/models.py` | The `Report` record shape and the `AppConfig` settings schema |
| Sample data | `tech_marketplace/data_source.py` | The built-in synthetic catalog + loaders for JSON/CSV/in-memory data |
| Template | `tech_marketplace/templates/marketplace.html.j2` | The HTML/CSS/JS shell, parameterized by config |
| Renderer | `tech_marketplace/renderer.py` | Combines config + data + template into the final HTML file |
| CLI | `tech_marketplace/cli.py` | `python -m tech_marketplace ...` command-line usage |

The generated page is fully client-side (vanilla JS, no build step,
no framework, no external requests required at view-time) — open the
output `.html` file directly in a browser, or host it on any static
file server / SharePoint page / intranet portal.

## Quick start

```bash
pip install jinja2   # the only runtime dependency
python generate_dashboard.py
```

This writes `technology_analytics_marketplace_dashboard.html` in the
current directory using the built-in sample catalog and default
theme. Open it in a browser.

## Customizing everything

Nothing about branding, color, icons, copy, or links is hardcoded in
the template — it all flows from an `AppConfig` (see
`tech_marketplace/models.py::DEFAULT_CONFIG` for the full schema with
inline documentation for every field). Override only what you need in
a JSON file:

```bash
python generate_dashboard.py --config config.example.json --output dashboard.html
```

`config.example.json` shows every section:

- **`branding`** — page title, hero heading/copy, optional logo image
  URL, favicon URL (any image URL or `data:` URI), footer text.
- **`theme`** — every CSS color variable (`brand`, `brand_dark`, `bg`,
  `card`, `text`, `muted`, `border`, `success`, `warning`, `danger`,
  `purple`) plus `font_family`. Change `theme.brand` alone to re-skin
  every button/link/accent in one line.
- **`icons`** — the search box glyph, the "open" arrow, the "top
  match" star, and the owner-avatar gradient colors. Swap in emoji,
  different Unicode glyphs, or leave as-is.
- **`search`** — the search box placeholder, the clear-button label,
  and the list of clickable natural-language example prompts.
- **`labels`** — every other piece of on-page copy: section headings,
  button text, empty-state message, metric tile captions, the "why
  this matched" phrasing. Useful for localization/rewording without
  touching HTML.
- **`data`** — `base_url` (a prefix auto-applied to any relative
  report URL, so re-pointing an entire catalog at a new BI portal
  root is a one-line change), plus how many cards get badges/appear
  in each rail (`top_match_count`, `recommended_count`,
  `popular_count`, `owners_count`).

You only need to specify the keys you want to change — everything
else falls back to the built-in default (a deep-merge, see
`models.deep_merge`).

## Customizing the catalog (reports/dashboards)

Bring your own catalog instead of the synthetic sample data:

```bash
python generate_dashboard.py --reports reports.example.json --output dashboard.html
```

Reports can come from:

- A **JSON file**: a list of objects (or `{"reports": [...]}`), shape
  shown in `reports.example.json`. Fields mirror
  `tech_marketplace.models.Report` — `id`, `name`, `domain`, `owner`,
  `contact`, `platform`, `last_refresh` (or legacy `lastRefresh`),
  `views`, `rating`, `accent` (hex color), `description`, `keywords`
  (list — the biggest lever for good natural-language search),
  `tags` (list), `url`.
- A **CSV file**: same columns; `keywords`/`tags` use `|` as the
  in-cell list delimiter (e.g. `cloud|cost|finops`).
- **In-memory Python data** — call the library directly instead of
  the CLI (see below) and pass a `list[dict]` or `list[Report]`
  straight from an API call, database query, or SharePoint export.

Relative `url` values (anything not starting with `http(s)://`, `/`,
or `#`) are automatically combined with `data.base_url` from your
config, so a whole catalog's links can be repointed without editing
every row.

## Using it as a library

```python
from tech_marketplace import AppConfig, load_reports, MarketplaceRenderer

config = AppConfig.from_overrides({
    "theme": {"brand": "#8764b8", "brand_dark": "#5b3d85"},
    "branding": {"hero_title": "Find any Contoso dashboard in seconds."},
})

reports = load_reports("reports.example.json", base_url="https://contoso.example/reports")

MarketplaceRenderer(config, reports).build("dashboard.html")
```

Or, for the common case, the one-call helper:

```python
from tech_marketplace import build_dashboard

build_dashboard(
    config_path="config.example.json",
    reports_path="reports.example.json",
    output_path="dashboard.html",
)
```

## CLI reference

```
python -m tech_marketplace --help

  --config PATH     JSON file of AppConfig overrides
  --reports PATH     JSON or CSV file of reports
  --output PATH       Output HTML file path (default: technology_analytics_marketplace_dashboard.html)
  --base-url URL      Shortcut for data.base_url without a config file
```

## What the generated page can do

Ported feature-for-feature from the original prototype, all
client-side after the one-time Python render:

- Live search-as-you-type with a lightweight relevance-scoring
  algorithm (name/domain/description/keyword/tag weighting + token
  matching so natural-language questions work).
- Clickable "Try:" example-query chips.
- Capability/domain filter chips, generated automatically from
  whatever tags exist in the loaded catalog.
- Result cards with a CSS-only "mini dashboard" snapshot preview,
  a larger hover preview, metadata grid (owner/platform/refresh/
  views), a "why this matched" explanation, and quick actions
  ("Open", "Show related", "Find by owner").
- A sticky right rail: recommended-for-your-search, most-viewed, and
  owner contact cards.
- Responsive layout down to mobile widths.
- Fully keyboard-accessible search input with an `aria-label`.

## Extending further

- **New data source**: add a loader function in `data_source.py`
  (e.g. a REST API pull) that returns `list[Report]`, and pass it to
  `MarketplaceRenderer` directly — you don't need the CLI/file-based
  path at all.
- **New theme tokens**: add a key under `theme` in
  `models.DEFAULT_CONFIG`; `AppConfig.css_variables()` picks up any
  new key automatically as a `--kebab-case` CSS custom property, no
  template change required (reference it in the template's `<style>`
  block via `var(--your-key)`).
- **New on-page copy**: add a key under `labels` in
  `DEFAULT_CONFIG`, reference it in the template as
  `{{ labels.your_key }}` (server-rendered) or via `TEXT.your_key` in
  the `<script>` block (client-rendered).
