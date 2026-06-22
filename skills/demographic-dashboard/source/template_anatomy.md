# Template anatomy

`assets/template.html` is the standardized skeleton. This document explains its sections, its placeholders, and the runtime API that custom charts can use.

## Sections, top to bottom

1. **`<head>`**
   - `<html lang="{{LANG}}" dir="{{DIR}}">` for language and direction.
   - Google Fonts link for Heebo (400/500/700/900).
   - Tailwind CDN (`cdn.tailwindcss.com`).
   - Chart.js CDN (`cdn.jsdelivr.net/npm/chart.js`).
   - Small `<style>` block for: custom scrollbars on tables, `card-hover` transition, tab active state, toggle-button active/inactive states.

2. **Header bar** (`<header>`):
   - Logo `<img src="{{LOGO_PATH}}">` left-aligned in RTL (visually at the right).
   - Title `{{TITLE}}` and subtitle `{{SUBTITLE}}`.
   - KPI cards to the right (visually at the left in RTL). One card per KPI in the config.

3. **Filter + primary chart section** (`<section class="lg:col-span-8">`):
   - Sidebar of filters (dropdowns from the config's `filters` array, generated at build time).
   - Primary chart canvas, large, on the content side of the sidebar.

4. **Secondary chart sections** (`<section class="lg:col-span-4">`):
   - Stacked vertically, 300px tall each, one per chart in the config.
   - Each card supports optional toggle buttons (declared in the chart config as `toggles`).

5. **Data table section** (`<section class="lg:col-span-12">`):
   - Tab row at top, search box on the right.
   - Scrollable table body with virtualized rendering when row count > 500.

6. **Footer**: data source line from `{{DATA_SOURCE}}`.

7. **Modal** for drill-downs (hidden by default).

## Placeholders the builder fills

Double-curly-brace placeholders. The builder replaces these; the template alone is not a valid page.

- `{{LANG}}`, `{{DIR}}`, `{{TITLE}}`, `{{SUBTITLE}}`, `{{LOGO_PATH}}`, `{{DATA_SOURCE}}`, `{{ACCENT_COLOR}}`
- `{{KPI_BLOCKS}}`: generated HTML for KPI cards
- `{{FILTER_BLOCKS}}`: generated HTML for filter dropdowns
- `{{CHART_BLOCKS}}`: generated HTML shells for each chart (canvas or custom HTML)
- `{{TABLE_TABS}}`, `{{TABLE_HEADERS}}`: generated tab row and table header
- `{{DATA_JSON}}`: the serialized data block, embedded as a JS `const`
- `{{CONFIG_JSON}}`: the serialized config, minus schema-only fields
- `{{CUSTOM_JS}}`: concatenated JS from custom chart definitions
- `{{RUNTIME_JS}}`: the standard runtime (filters, KPI recalc, chart render loop)

The runtime JS lives in `assets/runtime.js` and is inlined at build time so the final HTML is self-contained.

## Runtime API (available to custom charts)

After page load, the runtime exposes these on `window.dashboard`:

- `window.dashboard.data`: the full raw data object keyed by table name.
- `window.dashboard.filteredData`: the currently filtered data, recomputed on every filter change.
- `window.dashboard.config`: the config JSON.
- `window.dashboard.onFilterChange(callback)`: register a callback that fires after filters change and `filteredData` is updated.
- `window.dashboard.registerChart(id, renderFn)`: register a custom chart's render function. `renderFn` receives `(filteredData, config)` and is called on initial load and every filter change.
- `window.dashboard.format(value, formatName)`: apply a declared format (`int_comma`, `pct1`, `pct0`, `currency_ils`, etc.).
- `window.dashboard.palette(kind, n)`: get a palette of `n` colors (`kind` in `sequential`, `qualitative`, `diverging`).

Custom charts should be registered, not immediately rendered. Registration ensures the chart participates in filter updates.

### Minimal custom-chart skeleton

```js
window.dashboard.registerChart("chart_age_pyramid", function(filtered, config) {
  const canvas = document.getElementById("pyramidChart");
  // build Chart.js config from `filtered`
  // destroy previous instance if present
  if (window.__pyramidChart) window.__pyramidChart.destroy();
  window.__pyramidChart = new Chart(canvas, { /* ... */ });
});
```

## What the template deliberately does not do

- **No router.** Single page, anchor navigation only.
- **No state in URL.** Filter state is not bookmarkable. If the user wants that, it is a follow-up feature.
- **No server.** Everything is client-side. `file://` works.
- **No localStorage.** Session-only by design; avoids stale state on re-open.
- **No per-user customization.** Template is uniform; config adapts content.

## When to modify the template vs the config

Modify the **config** for: titles, KPI list, filter list, chart list, color accents, table columns.

Modify a **custom chart block** in the config for: bespoke visualizations.

Modify the **template** for: structural changes that should propagate to every future dashboard (e.g., adding a standard "last updated" timestamp, changing the default font). Changes to the template are rare and should be discussed before making them, because they change the family look.
