# Demographics UI Kit — multi-resolution

A high-fidelity, interactive recreation of the Center's **settlement-resolution demographic dashboard**, reskinned into the brand system. This is the reference implementation for the *Data resolution model* in the root `README.md`.

Built from `source/demographic_dashboard_original.html` (real CBS data: 106 settlements, 18 authorities across the Eastern Galilee).

## Why this kit exists

It proves the system is **robust to data shape and resolution**. Where the education kit compares one authority against benchmarks, this kit handles a dataset that **nests down to individual villages** and aggregates back up — the user's core need ("show aggregated data, but be able to drill into each municipality and village").

## What it demonstrates

- **Drill-down filter cascade** — `רשות → מגזר → צורת יישוב → יישוב`. Each filter narrows the next; the specific-settlement dropdown only ever lists settlements that match the filters above it. Changing a parent resets the child. A **resolution chip** ("רזולוציה: יישוב") shows the current depth.
- **Aggregate-by-default** — lands on the whole-cluster view (190,338 residents, 106 settlements). The user narrows only if they want to.
- **Population pyramid** — age × gender, men rendered as negative (left) cyan bars, women as positive (right) magenta bars. Recomputes to whatever the filters select.
- **Segmented metric toggles** — the haredi-population card flips between `מועצות / יישובים` scope and `% / מספר` unit; the composition card flips `כללי / מפורט`. One chart, multiple framings.
- **Donut composition + click-to-drill** — clicking a settlement-type slice opens a modal listing the underlying settlements, sorted by population.
- **Weighted KPIs** — total population, settlement count, mean socio-economic rank, population-weighted mean wage.
- **Three-tab data table** — authorities / all settlements / settlements-with-haredi-population, each with a relevant column set, plus search.

## File map

```
ui_kits/demographics/
├── index.html   Layout: header, drill-down sidebar + pyramid, side charts, socio/wage, table, modal
├── app.js       Filter cascade, weighted aggregation, 5 chart renderers, modal, table
├── data.js      106 settlements + 4 regional councils, age bins, cleaned from the CBS source
├── mark.png     Mosaic brand mark
└── README.md    This file
```

## Robustness notes baked in

- **Zero-as-missing:** many kibbutz rows have `wage: 0` / `socio_rank: 0` (suppressed). The kit treats these as "no data" in weighted means rather than dragging the average to zero.
- **City vs. regional council:** the authorities table unions independent authorities (cities/local councils, which are also settlement rows) with the 4 regional councils (aggregates). The pyramid and KPIs always work off settlement rows so totals stay consistent.
- **Dirty-key tolerance:** the source had a typo'd key (`haredi_pctדד`); the extraction coerced numerics and ignored the noise.

## How to adapt for a new dataset (welfare, tourism, …)

1. Replace `data.js` with your cleaned rows. Keep the nesting columns (`authority`, `sector`, `type_gross`, plus your atomic name field).
2. Map your measures into the KPI row and the side charts. Keep the **aggregate-by-default + cascade** pattern.
3. Pick the accent for the topic (`egkc-accent-gold` for tourism, `-magenta` for welfare, etc.) on `<body>`.
4. Swap chart types to match your data shape per the *Data robustness* rules in `SKILL.md`.
