---
name: rkcg-design
description: Use this skill to generate well-branded interfaces, dashboards, and assets for the Regional Knowledge Center East | West Galilee (מרכז ידע אזורי גליל מזרחי | מערבי) — for production code or throwaway prototypes/mocks. Contains the canonical dashboard template, runtime, design tokens, type system, brand palette (drawn from the mosaic logo), real logo/mark assets, and a reusable UI kit for Hebrew RTL data-dashboard work covering demographics, education, welfare, tourism, and more. Invoke when the user wants any artifact in the RKCG visual family: a new dashboard from cleaned data, a custom chart block, a print-ready briefing, a slide deck cover, or a mock of a future section.
user-invocable: true
---

# RKCG Design

Read **`README.md`** in this skill first — it contains the brand context, content-fundamentals rules, visual-foundations rules, iconography guidance, and the canonical look (Heebo, slate-50, rounded-xl cards, blue accent, RTL Hebrew).

Then explore the other files as needed:

| File | When to read it |
|---|---|
| `README.md` | Always — sets the rules for everything else. |
| `colors_and_type.css` | Always — import this in any new HTML artifact. Defines tokens, type scale, formatter classes, and accent variants. |
| `source/canonical_template.html` | When building a new dashboard from scratch — this is the chrome that every EGKC dashboard inherits from. |
| `source/canonical_runtime.js` | When writing custom chart blocks — exposes `window.dashboard.{data, filteredData, registerChart, format, palette, normHe}`. |
| `source/original_SKILL.md`, `source/phase3_visualize.md`, `source/template_anatomy.md`, `source/hebrew_gotchas.md` | When generating a dashboard via the `excel-to-dashboard` pipeline (the upstream skill that produces these dashboards). |
| `ui_kits/dashboard/` | When recreating, demoing, or extending the **education** dashboard — a worked example: authority vs cluster vs national Bagrut comparison. |
| `ui_kits/demographics/` | When building **multi-resolution** dashboards (village → authority → cluster) — a worked example with drill-down filter cascade, population pyramid, segmented toggles, donut, and click-to-drill modal. |
| `preview/` | When iterating on design-token decisions — small specimen cards for every type, color, spacing, and component decision. |
| `assets/wordmark.svg`, `assets/monogram.svg` | When adding the brand mark to a new artifact. |
| `fonts/` | When taking a dashboard offline or to print — see `fonts/README.md` for the self-hosting flow. |

## What to do when invoked

- **If creating visual artifacts** (slides, mocks, throwaway prototypes, embedded reports): copy `colors_and_type.css`, the wordmark/monogram, and any `ui_kits/dashboard/*.{html,js}` files you need into the output, then build a static HTML file the user can view directly. Stay inside the visual foundations described in `README.md` — Heebo, slate-50, rounded-xl, one accent per artifact, no decorative icons.
- **If working on production code**: read the rules in `README.md` and `colors_and_type.css` to become an expert in the brand. Reference `source/canonical_template.html` for the structural skeleton; use the runtime API exposed in `source/canonical_runtime.js` for any custom chart.
- **If the user invokes this skill without further guidance**: ask what they want to build (a new dashboard? a briefing slide? a custom chart block? a print export?), ask for the data and the question the artifact should answer (see *Phase 0: Orient* in `source/original_SKILL.md`), ask about the accent color and any sensitive columns, then act as the brand's expert designer and produce HTML artifacts or production code as needed.

## Hard rules (do not violate without flagging)

1. **Language & direction.** Hebrew, `dir="rtl"`. Hebrew quotation marks (״) for abbreviations.
2. **Voice.** Civic-formal, third-person, no exclamation marks, no emoji, no em-dashes, no marketing superlatives. Titles describe what is shown, not what to feel.
3. **Typography.** Heebo only. Weights 300/400/500/700/900. No competing display face. (The older 03_viz used Assistant — that was one-off; new work uses Heebo.)
4. **Color.** Slate-50 background, white surfaces, one accent per artifact picked from the brand-mosaic 6-color family (`egkc-accent-{cyan,navy,blue,lime,gold,magenta}`). All colors are drawn directly from the mosaic logo. There is no red in the brand — use magenta for sensitive / negative-axis communication.
5. **Chart palette.** Use the runtime's `palette()` helper or the `--egkc-q-*` / `--egkc-s-*` / `--egkc-d-*` CSS vars — qualitative for unordered, sequential for ordered, diverging for signed.
6. **Sorting.** Never alphabetize a categorical axis (Hebrew locale collation is non-obvious). Sort by measure descending unless the dimension has a natural order (then ascending by dimension).
7. **Privacy.** If the data was suppressed below n<11, include the *"לא מוצגים מוסדות עם פחות מ-11 נבחנים…"* footnote near every visualization.
8. **Surfaces.** `bg-white rounded-xl shadow-sm p-6` for chart cards, `rounded-lg p-4` for KPI cards. No gradients, no glass, no backdrop-blur.
9. **Iconography.** None by default. If needed, Lucide at stroke-1.5 (flagged substitution — not formally adopted).
10. **Logo.** Use `assets/logo.jpg` (full bilingual lockup) on splash/cover surfaces, and `assets/mark.png` (mosaic mark alone) inside dashboard headers and anywhere the wordmark is too wide. Never recolor the mark; never re-typeset the wordmark; leave one tile-height of clear space around it.

## Data robustness — handle any input

The Center's data spans education, demographics, welfare, tourism, employment, and budgets, at resolutions from national down to single village. A dashboard built with this system must be **robust to the shape of the input**:

1. **Detect the resolution levels present.** Look for nesting columns: national / cluster (אשכול) / authority (רשות) / settlement (יישוב). Not every dataset has all four — degrade gracefully.
2. **Aggregate by default, drill on demand.** Land on the highest aggregate (cluster or whole-dataset). Let the user narrow via a **cascading filter stack** where each filter narrows the next (e.g. Authority -> Sector -> Type), hiding options that are not present in the filtered subset. Changing a parent resets its children. This is the user's primary use: *showing aggregated results*, with optional drill-down.
3. **Weight every aggregation** by population / examinees / the natural denominator — never a naive mean of means.
4. **Show a resolution chip** so the reader always knows what level they're seeing; recompute KPIs + charts to match.
5. **Cities vs. regional councils:** an עירייה / מועצה מקומית is both an authority and a settlement row; a מועצה אזורית is an authority equal to the weighted aggregate of its settlements. Treat both.
6. **Pick chart types by data shape:** age×gender → population pyramid (mirrored horizontal bars, men negative); composition → donut (click slice → drill modal); ranked comparison → horizontal bars with a benchmark line; metric that has two framings (%/abs, gross/detailed) → segmented in-card toggle, don't split into two charts.
7. **Document calculations:** Any graph presenting calculated or aggregated data MUST include a clear textual explanation beneath it of how the calculation was performed (e.g., "Dependency ratio calculated as (0-14 + 65+) / (15-64)").
8. **Clean Hebrew inputs** (gershayim, RTL, stray keys, zero-as-missing) before display — see `source/hebrew_gotchas.md`. The demographic source even had a typo'd key (`haredi_pctדד`); robust parsing coerces and ignores noise.

See `ui_kits/demographics/` for the reference implementation of all seven.

## Quick-start patterns

### A new dashboard from cleaned data
Run the upstream `excel-to-dashboard` pipeline (see `source/original_SKILL.md`). Its output is a single-file HTML that already conforms to this design system.

### A custom chart inside an existing dashboard
Use `"type": "custom"` in the dashboard config and provide `html` + `js` inline. Register your render function via `window.dashboard.registerChart(id, fn)` so it participates in filter updates.

### A mock or briefing slide
Start a new HTML file. Import `colors_and_type.css`. Put your work inside `<body class="egkc-accent-blue">` (or another accent). Wrap content in `<div class="egkc-card">` for sections. Use the semantic type classes (`egkc-h1`, `egkc-subtitle`, `egkc-label`, `egkc-caveat`). Follow the content rules.

### A new section to add to the canonical template
Mock it in `preview/` first as a ~700×N card. Confirm with the team. Then port the structural changes into `source/canonical_template.html` (rare — changes propagate to every future dashboard).
