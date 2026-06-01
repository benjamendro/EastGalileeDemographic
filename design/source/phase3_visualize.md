# Phase 3: Visualize reference

Read this when writing the dashboard config JSON. The config is consumed by `scripts/build_dashboard.py` which merges it with the data and the template.

## Config schema

```jsonc
{
  "meta": {
    "title": "דשבורד דמוגרפי גליל מזרחי",
    "subtitle": "מערכת ניתוח דמוגרפי וכלכלי",
    "logo_path": "images/logo.png",
    "data_source": "מקור הנתונים: הלשכה המרכזית לסטטיסטיקה (הלמ\"ס), 2023",
    "lang": "he",
    "dir": "rtl",
    "accent_color": "#2563eb"
  },

  "data": {
    "primary_table": "settlements",
    "tables": {
      "settlements": "outputs/<run-id>/02_clean/cleaned.csv",
      "authorities": "outputs/<run-id>/02_clean/authorities.csv"
    }
  },

  "kpis": [
    { "id": "kpi_population", "label": "סה\"כ אוכלוסייה",
      "type": "sum", "column": "population", "format": "int_comma" },
    { "id": "kpi_count", "label": "מספר יישובים", "type": "count" }
  ],

  "filters": [
    { "id": "f_authority", "label": "רשות מוניציפלית",
      "column": "authority", "type": "select", "include_all": true },
    { "id": "f_sector", "label": "מגזר",
      "column": "sector", "type": "select", "include_all": true,
      "depends_on": null },
    { "id": "f_type", "label": "צורת יישוב",
      "column": "type_detailed", "type": "select", "include_all": true,
      "depends_on": "f_sector" }
  ],

  "charts": [
    {
      "id": "chart_sector_distribution",
      "title": "אוכלוסייה לפי מגזר",
      "type": "bar",
      "orientation": "horizontal",
      "dimension": "sector",
      "measure": "population",
      "aggregation": "sum",
      "sort": "measure_desc",
      "max_categories": 20,
      "rare_bucket_label": "אחר",
      "show_data_labels": true,
      "section_size": "md"
    },
    {
      "id": "chart_socio_rank",
      "title": "התפלגות דירוג סוציו־אקונומי",
      "type": "bar",
      "dimension": "socio_rank",
      "measure": null,
      "aggregation": "count",
      "sort": "dimension_asc",
      "section_size": "sm"
    },
    {
      "id": "chart_age_pyramid",
      "title": "פירמידת גילים ומגדר",
      "type": "custom",
      "section_size": "lg",
      "html": "<div class='relative flex-grow min-h-[350px]'><canvas id='pyramidChart'></canvas></div>",
      "js_requires": ["chart.js"],
      "js": "/* inline Chart.js spec for the pyramid; receives filtered data */"
    }
  ],

  "table": {
    "tabs": [
      { "id": "tab_settlements", "label": "יישובים",
        "source": "settlements",
        "columns": ["name", "authority", "sector", "population", "socio_rank"],
        "default": true },
      { "id": "tab_authorities", "label": "רשויות",
        "source": "authorities",
        "columns": ["name", "type_gross", "population_sum"] }
    ],
    "search_columns": ["name", "authority"]
  }
}
```

## Chart selection by column semantics

### One categorical, one numeric

- Cardinality ≤ 10: horizontal bar sorted by measure descending. Show data labels.
- Cardinality 11 to 30: vertical bar sorted by measure descending, rotate labels only if needed.
- Cardinality > 30: truncate to top N + rare bucket, same horizontal bar. If the user needs all categories, use the table, not a chart.

### One ordinal, one numeric

Bar chart sorted by **dimension** ascending (the natural order), not by measure. This is the exception to "always sort by value". State the order in the chart subtitle.

### Two categoricals

Heatmap if both are low-cardinality. Stacked bar if one is much higher cardinality than the other (the high-cardinality one is the x-axis, the low one is the stack). Grouped bar only if both have ≤ 5 categories.

### One numeric alone

Histogram with declared bins (not auto), or box plot if you care about outliers. Never a pie chart for a distribution.

### Two numerics

Scatter with optional color by a third (categorical) dimension. If n > 2000, hex bin or density.

### Time + numeric

Line. Always line. No area unless the numeric is a composition that must sum to a whole.

### Never-do list

- Pie charts with more than 5 slices. Use a bar instead.
- 3D charts in general.
- Sorted alphabetically on categoricals (see below).
- Dual y-axes unless both measures are the same unit on different scales that have to share the x-axis. It misleads 90 percent of readers.

## Sort order policy

Default: sort categoricals by the measure, descending.

Exceptions: ordered dimensions (dates, ordinal categories with a declared order, numeric bins) sort by the dimension. Declare the exception in the chart config so the builder does not default.

Never alphabetize a categorical axis. Hebrew alphabetization in JavaScript depends on the locale and produces visually surprising order (letters like "ך" vs "כ" sort in ways non-experts do not expect). Always sort by measure.

## Label policy

- If labels exceed 20 characters at the rendered size, truncate with a trailing ellipsis and show the full label on hover/tooltip. Do not rotate labels as the primary solution.
- Numeric labels in thousands get comma separators (`int_comma` format in the config).
- Percentages display with one decimal unless the user declares otherwise.
- Hebrew labels with embedded Latin-script text inside must preserve direction; the template's CSS handles `<bdo>` and `<span dir>` if you wrap in the chart config's custom label function.

## Color policy

- Ordered dimension (ordinal, binned numeric): sequential palette, light-to-dark in the order direction (ColorBrewer Blues, Greens, etc.).
- Unordered categorical: qualitative palette (8 distinct hues max). If more categories are unavoidable, repeat with lighter fills rather than introducing low-contrast hues.
- Signed numeric (diff from baseline, year-over-year change): diverging palette centered on zero.
- Avoid red-green as the only distinction; 4-8 percent of men have red-green colorblindness.

## Filter design

Filters update every chart and KPI in real time. The config's `filters` array declares order and dependencies.

- `depends_on`: when filter B depends on filter A, B's options are computed from the rows matching A. This is what makes "select authority then see only its settlements" work.
- Always include a reset button (the template does this automatically).
- If a filter is only relevant to one chart, do not put it in the global sidebar. Add chart-local toggle buttons instead (the template supports them; see the toggle buttons in the sample template's Haredi chart).

## KPI design

KPIs live at the top. Three rules:
1. No more than 4 KPIs; the user cannot scan more than that at a glance.
2. Every KPI recalculates when filters change. The template handles this; the config just declares the aggregation.
3. A KPI is either a count, a sum, a mean, or a ratio. "Change since last year" is not a KPI unless you have a time dimension; it is a chart.

## Section layout

The template has a 12-column grid. Sections claim `lg:col-span-*` widths. The builder lays out charts in declared order, wrapping to new rows based on `section_size`:
- `sm`: 4 columns
- `md`: 6 columns
- `lg`: 8 columns
- `full`: 12 columns

Put the primary chart first and wide. Secondary breakdowns follow in smaller sections. Tables go last.

## Custom charts

If the chart needed is bespoke (age pyramid, Sankey, choropleth-like cell matrix, radar), use `"type": "custom"` and provide the HTML + JS inline. The JS runs in the template's scope and receives the filtered data as `window.filteredData`. See `references/template_anatomy.md` for what functions and data are available at runtime.

Writing custom charts is fine; the template is the chrome, not a straitjacket. But if you find yourself writing a custom chart for something that should have been a bar, reconsider.

## Bad dashboard tells

These are signals that the config is wrong, not that the data is boring:

- Three or more charts show nearly the same information. Consolidate.
- A chart where every bar is almost the same height. The dimension is not discriminating; drop it.
- A filter that has only one non-empty value. Drop it.
- A KPI that does not change when filters change. Move it to the footer as a dataset-level fact.
- Vertical bars with rotated labels. Use horizontal bars.
- Legend with more than 10 entries. Split the chart or aggregate.

The dashboard should let a person answer a question faster than scanning the raw data. If it does not, it is decoration.
