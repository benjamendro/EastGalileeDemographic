# EGKC Dashboard UI Kit

A high-fidelity, interactive recreation of the canonical EGKC dashboard, populated with real **Bagrut תשפ״ד** data for the **Eastern Galilee Cluster** (13 authorities, 8 core subjects).

## What it shows

The product question this dashboard answers:

> **"How does my municipality do in core Bagrut subjects, compared to the rest of the cluster, and to the national average?"**

That's exactly what the user asked for in the spec.

## Interactive features

- **Filters** (sidebar):
  - `רשות מוניציפלית` — 13 authorities in the Eastern Galilee Cluster
  - `מקצוע` — 8 core subjects (math, English, biology, physics, chemistry, computer science, history, civics)
  - `יחידות לימוד` — segmented control: 3 / 4 / 5
- **KPIs**:
  - Selected authority's weighted-average score (tinted accent card)
  - Cluster average (slate)
  - National average (slate)
  - Signed gap vs national (green if +0.5+, red if -0.5-, neutral else)
- **Charts**:
  1. **Headline** — grouped bars across all 8 core subjects, three series: authority / cluster mean / national. Headline answers "is my authority above or below the line, and on which subjects?"
  2. **Ranked authorities** — horizontal bars of all 13 authorities for the selected subject, with the selected authority highlighted in accent blue and a dashed red line at the national average.
  3. **Yehidot mix** — examinee counts at 3/4/5 yehidot for the selected authority. High share at 5 = excellence.
- **Data table tabs**:
  - `תוצאות לפי רשות` — authority × subject matrix at the selected yehidot level, with ▲/▼ markers vs national + cluster/national rows in the footer.
  - `פירוט הרשות הנבחרת` — every (subject, yehidot) row for the selected authority, with side-by-side cluster, national, and signed gap.

## File map

```
ui_kits/dashboard/
├── index.html         Layout + filter sidebar + chart shells + table + footer
├── app.js             Filter state, render functions for KPIs / charts / table
├── data.js            Real Bagrut data subset (13 authorities × 8 subjects × 3 yls + national)
└── README.md          This file
```

## How it maps to the canonical template

The kit follows `source/canonical_template.html` section-for-section. The runtime is split out into `app.js` for readability (the production builder inlines it). Tokens come from `colors_and_type.css`. Heebo loads from Google Fonts CDN through the stylesheet.

## How to extend

- **Add a chart** — drop a new `lg:col-span-N` block into the secondary chart grid; write a `chart<Name>()` function in `app.js`; call it from `render()`.
- **Add a filter** — add a `<select>` in the sidebar; bind a state field; have your chart functions read from `state`.
- **Change the accent** — flip the `body` class from `egkc-accent-blue` to `egkc-accent-emerald` / `-amber` / etc.

## Data lineage

Real `שנת תשפ״ד` results extracted from `source/03_viz_original.html` (which itself came from a Freedom of Information request to the Ministry of Education). The data subset is curated to: cluster `גליל מזרחי` only; core subjects only; national baselines included. Authorities with fewer than 11 examinees in a subject are not present in the source per the privacy threshold.
