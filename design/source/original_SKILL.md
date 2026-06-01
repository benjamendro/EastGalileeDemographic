---
name: excel-to-dashboard
description: End-to-end workflow for turning an arbitrary Excel file (clean or messy, usually Hebrew) into a standardized, filterable single-file HTML dashboard with a data-quality audit, cleaning and feature encoding, chart selection, and QA on both the data and the rendered web output. Use this skill whenever the user supplies an .xlsx/.xls/.csv and wants any combination of: profiling the file, cleaning or reshaping it, encoding categorical features, building an interactive dashboard, or auditing either the data or the final page. Also use it when the user mentions dashboards, HTML reports from tabular data, Hebrew dashboards, RTL visualizations, text-to-columns, free-text clustering, one-hot encoding for analysis, or QA checks on a web report, even if they do not name all four phases explicitly.
---

# Excel to Dashboard

A four-phase workflow that takes a tabular file and produces a standardized, interactive, Hebrew-friendly HTML dashboard along with an auditable trail of what was found, what was changed, what was encoded, and what was verified.

## Quick start

For the common case, use the orchestrator:

```bash
python scripts/run_pipeline.py \
    --input path/to/input.xlsx \
    --run-id my_run \
    --specs path/to/specs/
```

The specs directory should contain `cleaning_spec.json`, `dashboard_config.json`, and optionally `qa_spec.json`. Outputs land in `outputs/<run-id>/` as `01_audit/`, `02_clean/`, `03_viz/index.html`, `04_qa/`. If you omit `--specs` the orchestrator runs audit-only; you then write specs from the audit findings and re-run.

For debugging or partial runs, each phase has its own script; see the reference map at the bottom.

## Why this exists

Tabular data arrives in every possible state of disrepair: merged cells, multi-row headers, free-text columns that should be categorical, numbers stored as strings, mixed Hebrew and English, footer totals glued to the bottom of the data, duplicate rows from copy-paste, encoding confusion. Going straight from a raw file to a chart is how you get charts that lie.

This skill enforces a sequence: **understand → clean → encode → visualize → verify**. Each phase produces an artifact (a profile, a cleaned dataframe, a config, an HTML, a QA report) so the user can audit any step and roll back.

The visual output conforms to a standardized template (see `assets/template.html` and `references/template_anatomy.md`) so dashboards from different projects feel like part of one family, while the chart selection and filter design adapt to each dataset.

## When to use, when not to

Use this skill when the input is a tabular file (.xlsx, .xls, .csv, .tsv) and the desired output involves any of: a profile report, a cleaned version, an encoded version, a dashboard, or QA on such a dashboard.

Do not use this skill for: parsing PDFs (use the pdf skill instead), building slide decks (pptx skill), GIS/spatial rasters, database ETL pipelines without a final HTML deliverable, or pure Python data-science scripting tasks where no user-facing output is produced.

If the user asks only for phase 3 ("make me a dashboard from this cleaned CSV"), skip phases 1-2 but still run phase 4 at the end. Be explicit with the user about which phases you are skipping and why.

## Workflow

### Phase 0: Orient

Before anything else, ask the user what they want the dashboard to answer, in one sentence if they can manage it. A dashboard is a lens on a question; without the question, chart selection degenerates into "show every column". If the user cannot articulate a question, offer to propose one after phase 1 (you will know the data by then).

Also confirm: the language of the dashboard (default: Hebrew RTL), whether the output is a single-file self-contained HTML (default: yes), and whether any columns are sensitive (names, national IDs, addresses) and need masking.

### Phase 1: Audit the file

Run `scripts/audit_excel.py` on the input file. This produces a JSON profile and a human-readable Markdown summary covering:

- Sheets and their sizes
- Detected header row(s), including multi-row header hints
- Per-column: inferred dtype, null rate, unique count, sample values, suspected free text vs categorical, mixed-content indicators (e.g., "numbers-with-units-glued-on")
- Hebrew-specific issues: mixed directionality, stray niqqud, inconsistent whitespace, bidi control chars, non-canonical punctuation
- Structural hazards: merged cells, footer totals, hidden rows/columns, empty leading rows
- Candidate keys and referential sanity between columns

**Read `references/phase1_audit.md`** before interpreting the profile. It explains what each finding means and which ones are blocking vs cosmetic.

Report findings to the user before cleaning. Do not silently fix things. If the file is unusable (e.g., no consistent header can be found, or the sheet is a pivot table rather than a data table), say so and stop.

### Phase 2: Clean and encode

Two sub-steps, both driven by a plan you write after phase 1 and confirm with the user.

**2a. Clean.** Run `scripts/clean_excel.py` with a cleaning spec JSON. The spec describes: header row(s) to use, columns to drop, text-to-columns splits (regex or delimiter), type coercions, null-token normalizations (Hebrew strings like "לא רלוונטי" or "-" treated as null), trimming and whitespace policy, footer row removal, drop-duplicates. Output: a cleaned CSV + a schema sidecar + a cleaning diff report.

**2b. Encoding and clustering are optional utilities.** They are not part of the main dashboard path; use them when the downstream task needs encoded features (ML prep) or when a free-text column needs grouping before it can be charted.
- `scripts/encode_features.py`: onehot, ordinal, frequency, passthrough.
- `scripts/cluster_freetext.py`: normalized-exact or character-n-gram TF-IDF + DBSCAN (offline, no network dependency). Use before encoding any high-cardinality free-text column.

**Read `references/phase2_clean_encode.md`** before writing the cleaning spec. It covers the decision tree for cleaning operations, text-to-columns patterns for Hebrew data, and how encoding/clustering specs work if you need them.

Every transformation is logged. At the end of phase 2 you have: a cleaned CSV and a changelog. Hand both to phase 3.

### Phase 3: Visualize

Produce a dashboard config JSON, then run `scripts/build_dashboard.py` to merge config + data + template into a single `index.html`.

The config describes: meta (title, subtitle, logo path, data source line, language, direction), KPIs (count, sum, mean, ratio, card-style top-of-page), filters (column-driven dropdowns with dependency graph), charts (type, dimension, measure, aggregation, sort order, label policy), table (visible columns, search columns, tabs).

**Read `references/phase3_visualize.md`** before writing the config. It covers: chart selection by column semantics (cardinality, dtype, skew, dimension count), sort-order policy (most-to-least unless the dimension has a natural order, never alphabetical on categoricals), label policy (truncate + tooltip, not ellipsis), color policy (ColorBrewer ordinal for ordered categoricals, qualitative palette for unordered, diverging for signed metrics), and when to write a bespoke chart as a `custom` block rather than using a generic type.

For bespoke charts (e.g., age pyramid, choropleth-like cell matrix, Sankey), use `{"type": "custom", "html": "...", "js": "..."}` in the config and write the Chart.js spec inline. The builder injects them into the standard chrome. Do not abandon the template to hand-roll a full HTML.

Everything is single-file by default: data is embedded as a JSON block in `<script>`, Tailwind and Chart.js come from CDN, Heebo from Google Fonts. If the user needs an offline-capable build, pass `--offline` to the builder and it will inline the CDN assets.

### Phase 4: QA

Two tracks, both required.

**4a. Data QA.** Run `scripts/qa_data.py` against the cleaned and encoded outputs. It checks: schema (declared vs actual), null rates against thresholds, duplicates on declared keys, type drift, referential integrity (e.g., every `authority` in the detail table must appear in the authority list), numeric-range sanity (e.g., percentages in [0, 100]), category cardinality not exploded by encoding, and reconciliation (e.g., `sum(population_by_settlement) == sum(population_by_authority)`).

**4b. Web QA.** Run `scripts/qa_web.py` against the generated HTML. Two tiers depending on environment:

- **Static tier (always runs):** parses the HTML + extracts the embedded data JSON. Verifies: data block parses as valid JSON, every filter `id` has a matching column, every chart's referenced columns exist, every KPI calculation is well-formed, no `undefined` leaks into visible text, Hebrew text renders with correct direction attributes, image paths exist on disk, footer data-source line is non-empty.
- **Browser tier (if Playwright is available):** launches the page headless, waits for Chart.js to finish, checks for console errors, takes a screenshot, then interacts: picks each filter option in turn and verifies the visible row count and KPI values change and reconcile. This catches the class of bugs that static checks miss, like a filter that silently does nothing.

**Read `references/phase4_qa.md`** for the full check list and how to interpret failures. A failing check is not always a bug; sometimes the spec is wrong. The QA report distinguishes violations ("the data disagrees with itself") from policy gaps ("no null threshold was declared for this column").

If any violation is found, return to the earliest offending phase, not phase 3. Fixing a data bug by hiding it in the viz is how dashboards lie.

## Outputs

Every run of the skill produces, in the working directory under `outputs/<run-id>/`:

- `01_audit/profile.json`, `01_audit/summary.md`
- `02_clean/cleaned.csv`, `02_clean/cleaned.schema.json`, `02_clean/cleaning_spec.json`, `02_clean/diff.md`
- `03_viz/config.json`, `03_viz/index.html`
- `04_qa/data_report.md`, `04_qa/web_report.md`, `04_qa/screenshot.png` (if browser tier ran)

Optional sub-directories when encoding or clustering is used:
- `02_encode/encoded.csv`, `02_encode/encoded.schema.json`, `02_encode/mapping.json`
- `02_cluster/clustered.csv`, `02_cluster/cluster_report.md`

The user gets `index.html` as the headline artifact. The rest is evidence.

## Hebrew and RTL: the non-negotiables

Read `references/hebrew_gotchas.md` in full before phase 2 if the data is Hebrew. Short version:

- `dir="rtl"` on `<html>`, Heebo font family, set `lang="he"` for accessibility
- Normalize Unicode to NFC before comparing or grouping Hebrew strings
- Strip niqqud (combining marks U+0591 to U+05C7) before matching unless the user says otherwise
- Treat zero-width characters (U+200E, U+200F, U+202A-U+202E, U+FEFF) as noise; strip them
- Never alphabetize categorical axes; Hebrew collation in JavaScript is locale-dependent and produces non-obvious order. Sort by measure value, descending, and state this in the chart subtitle
- Numbers, dates, and Latin-script proper nouns embedded in Hebrew text need explicit bidi handling; the template's base CSS gets this right for most cases but read the reference if anything looks wrong

## Interaction style

Be honest with the user at every phase handoff. If the data has irreparable problems (e.g., primary key that is not unique, critical column that is 80% null), say so instead of producing a polished dashboard on top of broken data. The dashboard is the last step, not the goal.

Do not use em-dashes in any prose you write for the user.

## Phase-by-phase reference map

| Phase | Primary script | Primary reference |
|-------|----------------|-------------------|
| Orchestrator (all phases) | `scripts/run_pipeline.py` | This SKILL.md |
| 1. Audit | `scripts/audit_excel.py` | `references/phase1_audit.md` |
| 2a. Clean | `scripts/clean_excel.py` | `references/phase2_clean_encode.md` |
| 2b. Encode (optional) | `scripts/encode_features.py` | `references/phase2_clean_encode.md` |
| 2b. Cluster (optional) | `scripts/cluster_freetext.py` | `references/phase2_clean_encode.md` |
| 3. Visualize | `scripts/build_dashboard.py` | `references/phase3_visualize.md`, `references/template_anatomy.md` |
| 4a. Data QA | `scripts/qa_data.py` | `references/phase4_qa.md` |
| 4b. Web QA | `scripts/qa_web.py` | `references/phase4_qa.md` |

All phases: `references/hebrew_gotchas.md` if working with Hebrew data.

## Stopping conditions

Stop and report to the user rather than continue, if:

- Phase 1 finds no consistent header row
- Phase 1 finds the sheet is a pivot table or presentation, not a data table
- Phase 2 proposed cleaning would drop more than 20 percent of rows
- Phase 2 encoding would create a one-hot column with cardinality > 200 (probably a free-text column that needs clustering first)
- Phase 4 data QA finds reconciliation failures that the user did not pre-accept

Stopping is cheap; silent corruption is expensive.
