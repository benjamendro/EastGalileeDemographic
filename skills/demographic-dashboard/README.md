# Regional Knowledge Center Galilee — Design System

מערכת עיצוב ל**מרכז ידע אזורי גליל מזרחי | מערבי** / Design system for the **Regional Knowledge Center East | West Galilee**.

## What this brand is

The **Regional Knowledge Center** (מרכז ידע אזורי) serves **two** regional cluster bodies in northern Israel — the **Eastern Galilee Cluster** (אשכול גליל מזרחי) and the **Western Galilee Cluster** (אשכול גליל מערבי). Together they cover dozens of local authorities across the region: Jewish, Arab, Druze, and Bedouin communities.

The Center produces **public-facing data analyses of Israeli national datasets** — Bagrut (matriculation) results, demographics, welfare, tourism, employment, budgets, more. The team turns messy government Excel files into **single-file HTML dashboards** that journalists, mayors, superintendents, and principals can open in a browser and explore.

The work is **civic-tech in tone**: serious, sourced, restrained. **Hebrew-first, RTL, desktop-primary.** The dashboards live alone — not inside a SaaS chrome — so the chrome IS the brand.

> "הנתונים עובדו על ידי מרכז הידע גליל מזרחי" — *Data processed by the Eastern Galilee Knowledge Center.*

## What this design system is for

**One product family: the EGKC Dashboard.** Every dashboard the Center publishes is generated from one [shared HTML template + runtime](source/canonical_template.html) via a four-phase pipeline (audit → clean → visualize → QA). The template is the design system's load-bearing component; everything else here exists to keep individual dashboards consistent with the family.

Use this system when you're:

- Generating a new dashboard from a cleaned dataset (most common).
- Designing a custom chart block that drops into an existing dashboard (`type: "custom"`).
- Producing a print export, briefing slide, or screenshot of a dashboard for a report.
- Mocking a new section before adding it to the canonical template.

## Source materials this is built from

- **`source/canonical_template.html`** — the canonical chrome (Heebo + slate-50 + rounded-xl cards + sidebar filters + 12-col chart grid + tab'd table). All future dashboards inherit from this.
- **`source/canonical_runtime.js`** — the filter / KPI / chart / table runtime. Defines palettes, formatters, normHe, aggregations.
- **`source/03_viz_original.html`** — one real dashboard (Bagrut Trends, Eastern Galilee Cluster, תשפ"ד). A **stylistic variant** that swapped Heebo→Assistant and rounded→squared. Useful as a content reference and as proof the template can be reskinned.
- **`source/original_SKILL.md`**, `source/phase3_visualize.md`, `source/template_anatomy.md`, `source/hebrew_gotchas.md` — the four-phase pipeline that produces dashboards. Read these before authoring a new dashboard config.
- **No Figma. No logo files.** The visual language below is **derived from the source code.** Substitutions are flagged at the bottom.

---

## Index — what's in this folder

| Path | What it is |
|---|---|
| `README.md` | This file — context, content rules, visual foundations, iconography. |
| `HOW_TO_USE.md` | Plain-language guide for handing this system to an AI agent to build a new dashboard. Start here if you're not a designer. |
| `SKILL.md` | Agent-Skills-compatible front matter — drop the folder into Claude Code and `egkc-design` is invocable. |
| `colors_and_type.css` | CSS variables — slate base, accent system, type scale, formatters as utility classes, Heebo `@font-face`. Import this into any new artifact. |
| `fonts/` | Heebo, self-hosted (woff2) so dashboards print and export consistently. |
| `preview/` | Cards rendered into the Design System tab: type, colors, spacing, components, brand. |
| `ui_kits/dashboard/` | When recreating, demoing, or extending the **education** dashboard — a high-fidelity worked example (authority vs cluster vs national Bagrut comparison) with real data, reusable JS, and a clear file split. |
| `ui_kits/demographics/` | When building **multi-resolution** dashboards — a worked example with **village-level drill-down**, population pyramid, segmented metric toggles, donut composition, and a click-to-drill modal. The reference implementation for the *Data resolution model*. |
| `assets/` | The official logo (`logo.jpg`) + cropped mosaic mark (`mark.png`). |
| `source/` | Read-only mirror of the originating codebase + skill references. |

---

## CONTENT FUNDAMENTALS

### Language & direction

**Hebrew, RTL.** Set `<html lang="he" dir="rtl">`. All UI strings — titles, labels, table headers, tooltip strings, axis labels, empty states, footer attribution — are in Hebrew. Numbers, Latin-script proper nouns (subject codes, school identifiers), and currency symbols stay LTR inside the RTL flow; the template handles bidi via CSS, but free-text from data should be normalized via `dashboard.normHe()` before display.

### Voice & register

**Civic-formal, restrained, sourced.** Closer to a government statistics bulletin than a SaaS dashboard. Copy reads like the captions on a Ministry of Education report.

**Titles describe what is being shown, not what the reader should feel:**

- ✅ *"ממוצע בגרות משוקלל (כללי)"* — "Weighted Bagrut average (overall)"
- ✅ *"התפלגות תלמידים לפי יח״ל באשכול (אחוזים)"* — "Student distribution by yehidot-limud (%)"
- ❌ *"רואים את הקפיצה?!"* — "See the jump?!"
- ❌ *"מספרים מרשימים!"* — "Impressive numbers!"

**Caveats sit near the chart they qualify, in smaller slate text:**

- *"מחושב כסך הנבחנים מתוך השכבה. קיימים פערים במקרים בהם נבחני י"א ניגשים למקצוע…"*
- *"לא מוצגים מוסדות עם פחות מ-11 נבחנים בהתאם להנחיות המקור."*

### Tone rules

- **Third-person, impersonal.** Never אתה/את ("you") or אנחנו ("we"). Subjects are *the data*, *the cluster*, *the authority*, *the student body*.
- **No exclamation marks. No emoji. No marketing superlatives.** Don't write "תובנות מדהימות!" — write the actual finding.
- **Quotation marks** are the Hebrew curly form (״) for abbreviations: יח״ל, תשפ״ד, סה״כ, בי״ס. Use straight quotes (") for actual quotation only.
- **Casing & punctuation:** Hebrew has no case. Headlines use Heebo weight 900 (black), not all-caps. Parentheses sit tight around qualifiers: `(כללי)`, `(אחוזים)`, `(מול ממוצע ארצי)`.
- **Numbers are precise, not rounded for vibes.** Scores show two decimals (`84.39`); percentages show one (`72.3%`); counts are integers formatted via `int_comma` (`13,308`).
- **Honor the privacy threshold.** Anywhere the underlying data was suppressed for `< 11` examinees, repeat that disclaimer near the visualization. Don't fabricate, infer, or interpolate.
- **No em-dashes** in any prose — the pipeline's SKILL.md explicitly bans them. Use a comma, a period, or a colon.
- **Reset language is direct, not cute:** `איפוס סינונים` ("Reset filters"), not `התחילו מההתחלה` ("Start over").

### Vocabulary cheatsheet

| Hebrew | Used for |
|---|---|
| בגרות | Matriculation exam / certificate |
| יח״ל (יחידות לימוד) | Study-unit level (2/3/4/5) — exam difficulty tier |
| אשכול | Cluster (regional authority cooperation) |
| רשות / רשויות | Local authority / authorities (municipalities) |
| מוסד / מוסדות | Institution / institutions (schools) |
| נבחנים | Examinees |
| מגזר | Sector (Jewish state, state-religious, Arab, Druze, Bedouin) |
| פיקוח | Supervision (which Ministry track) |
| זכאים | Eligible (for the certificate) |
| ממוצע משוקלל | Weighted average |
| ממוצע ארצי | National average |
| תצפיות מוצגות | Visible observations (row count under filters) |
| סינון / איפוס סינונים | Filter / reset filters |
| הכל | All (default option in a filter) |
| מקור הנתונים | Data source (footer attribution) |

### Verbatim copy library

These strings appear across dashboards and should be used as-is when contexts match.

- Attribution: *"הנתונים עובדו על ידי מרכז הידע גליל מזרחי"*
- Filter label: *"סינון"*
- Reset button: *"איפוס סינונים"*
- Row count: *"תצפיות מוצגות: "*
- All-option label: *"הכל"*
- Search placeholder: *"חיפוש..."*
- Privacy footnote: *"לא מוצגים מוסדות עם פחות מ-11 נבחנים בהתאם להנחיות המקור."*
- Empty state: *"לא נמצאו נתונים למקצוע וליח״ל הנבחרים"*
- Truncation footer: *`מוצגות {N} שורות ראשונות מתוך {TOTAL}`*

---

## VISUAL FOUNDATIONS

### The system at a glance

A **white-on-slate-50, rounded-xl, hairline-shadow** document. Heebo throughout, in weights 300/400/500/700/900. Cards are sheets of paper laid on a soft grey background. A single **accent color per dashboard** runs through the right edge of the header, the active tab underline, the reset link, and (optionally) the primary chart's bars. Everything else is slate.

The aesthetic is *credibility through plainness* — but unlike the 03_viz stylistic variant (Assistant + navy + bordered squares), the canonical look is **softer, more contemporary, more web-native**: rounded corners, subtle shadow elevation, generous whitespace. Think Israeli CBS bulletin rendered by a modern product team.

### Color — base

| Token | Hex | Where it shows up |
|---|---|---|
| `--egkc-bg-app` | `#f8fafc` (slate-50) | The page background. The only non-white surface. |
| `--egkc-surface` | `#ffffff` | Every card, header, sidebar, table. |
| `--egkc-fg-strong` | `#1e293b` (slate-800) | Body, KPI numbers, table cells. |
| `--egkc-fg` | `#334155` (slate-700) | Filter labels, sub-heads, hovered tab text. |
| `--egkc-fg-muted` | `#64748b` (slate-500) | Subtitles, axis ticks, caveats, inactive tabs. |
| `--egkc-fg-faint` | `#94a3b8` (slate-400) | Footer attribution, disabled states. |
| `--egkc-divider` | `#f1f5f9` (slate-100) | Hairline between sidebar and chart grid. |
| `--egkc-border` | `#e2e8f0` (slate-200) | Input borders, table cell separators. |

### Color — brand (from the mosaic logo)

The Center's logo is a **pixel mosaic** in 9 distinctive hues plus the wordmark navy. **These are the brand colors.** All accents and chart palettes are drawn directly from this mosaic so the dashboards visually belong to the Center.

| Token | Hex | What it is |
|---|---|---|
| `--egkc-navy`      | `#183048` | Deepest mosaic tile. The wordmark color. Use for H1 over white. |
| `--egkc-cyan`      | `#18a8c0` | Dominant mosaic tile. **Default accent.** |
| `--egkc-blue`      | `#1878a8` | Secondary mosaic blue. |
| `--egkc-cyan-deep` | `#186078` | Mid-deep teal — use as `--accent-strong`. |
| `--egkc-sky`       | `#48c0f0` | Bright sky tile. |
| `--egkc-sky-soft`  | `#78c0f0` | Pale sky tile. |
| `--egkc-lime`      | `#90c048` | Mosaic green. |
| `--egkc-gold`      | `#c0a860` | Mosaic gold/tan. |
| `--egkc-magenta`   | `#903078` | Mosaic plum/magenta. |

### Color — accent (per dashboard)

Each dashboard declares one `--accent`. **Default is brand cyan `#18a8c0`.** It paints:

- The 4px right border of the header (`.egkc-border-accent-edge`)
- The active tab underline + active tab text
- The "reset filters" link
- The selected-bar highlight in comparison charts
- The KPI numeral color in the tinted KPI card

Pick the per-dashboard accent from the **brand-derived 6-color family**:

| Accent | Hex | When | Body class |
|---|---|---|---|
| **Cyan (default)** | `#18a8c0` | Data / general / unspecified | `egkc-accent-cyan` |
| Navy | `#183048` | Policy / governance | `egkc-accent-navy` |
| Blue | `#1878a8` | Education / demographic | `egkc-accent-blue` |
| Lime | `#90c048` | Environment / agriculture | `egkc-accent-lime` |
| Gold | `#c0a860` | Tourism / economic | `egkc-accent-gold` |
| Magenta | `#903078` | Equity / welfare / sensitive | `egkc-accent-magenta` |

Never pick from outside the mosaic palette. If a topic genuinely needs a new accent, add it to the mosaic family first and document the addition here.

### Color — chart palettes

Defined in `colors_and_type.css` as CSS variables and in `source/canonical_runtime.js` as the JS `PALETTES` object. Exposed via `window.dashboard.palette(kind, n)`.

**Qualitative** (unordered categoricals, ≤10 hues) — **mosaic-derived**:
`#18a8c0` `#903078` `#1878a8` `#90c048` `#c0a860` `#183048` `#48c0f0` `#186078` `#78c0f0` `#d77b3a`

**Sequential** (ordered dimension; light→dark) — **brand cyan ramp**:
`#e6f6f9` `#c8eaf1` `#a0dbe7` `#78cad9` `#4ab7ca` `#18a8c0` `#1888a0` `#186078` `#183048`

**Diverging** (signed metric; centered at zero) — **magenta ⇢ neutral ⇢ cyan** (brand-aligned):
`#6b1f5a` `#903078` `#d5a8c8` `#e5e7eb` `#a0dbe7` `#18a8c0` `#186078`

> Note: the upstream `excel-to-dashboard` skill's `runtime.js` still ships the original generic Tailwind palette. New dashboards that load `colors_and_type.css` get the brand palette via CSS variables; if you want the JS `palette()` helper to return brand hues, override `PALETTES` after the runtime loads (one-line shim).

Rules:
- Ordered dimensions (ordinal, binned numeric) get **sequential**.
- Unordered get **qualitative**.
- Signed (delta-from-baseline) gets **diverging**.
- Never red/green as the only distinction — 4–8% of men can't read it. (The brand has no red anyway — use magenta/cyan as the diverging axis.)

### Type

- **Family:** **Heebo** (Google Fonts; OFL), a Hebrew-first sans by Oded Ezer + Meir Sadan, with Latin glyphs from Christian Robertson's Roboto. Self-hosted in `fonts/`.
- **Weights used:** 300 (light, sparingly), 400 (body), 500 (medium — filter labels), 700 (bold — section heads, table headers), 900 (black — H1 only).
- **Hierarchy:**

| Role | Size | Weight | Color |
|---|---|---|---|
| H1 / dashboard title | `text-3xl` (30px) | 900 black | `--fg-strong` |
| H2 / section head (inside card) | `text-lg` (18px) | 700 bold | `--fg` |
| H3 / sub-head | `text-base` (16px) | 700 bold | `--fg` |
| Filter label | `text-sm` (14px) | 500 medium | `--fg` |
| Body / table cell | `text-sm` (14px) | 400 regular | `--fg-strong` |
| Subtitle | `text-base` (16px) | 400 regular | `--fg-muted` |
| Caveat / footnote | `text-xs` (12px) | 400 regular | `--fg-muted` |
| KPI numeral | `text-3xl` (30px) | 700 bold | `--accent` (tinted on KPI bg) |
| Footer | `text-xs` (12px) | 400 regular | `--fg-faint` |

- **No monospace** — numbers use the same Heebo face. `tnum` (tabular nums) is enabled via CSS in the KPI cards so digits align.
- Hebrew & Latin set in the same family so embedded subject codes don't visually shift.

### Spacing

Tailwind's default 4px scale. The system uses:

- **Page outer padding:** `p-4 md:p-6` (16/24px)
- **Page max-width:** `max-w-7xl` (1280px), `mx-auto`
- **Card padding:** `p-6` (24px) for header & chart cards; `p-4` (16px) for KPI cards
- **Section gap:** `space-y-6` (24px) between header / filter+chart section / table / footer
- **Filter stack:** `space-y-3` (12px) between filter blocks
- **Chart grid:** `gap-4` (16px) between chart cells in the 12-col grid
- **Sidebar divider:** `md:border-l md:pl-4 border-slate-100` (1px hairline + 16px inset)

### Borders, corners, elevation

- **Corners:** `rounded-xl` (12px) for header, filter+chart section, chart cards. **`rounded-lg` (8px)** for KPI cards. **`rounded` (4px)** for inputs, buttons, table scrollbar thumb.
- **Shadows:**
  - `shadow-sm` — `0 1px 2px 0 rgba(0,0,0,0.05)` — every card at rest.
  - Hover lift (on `.card-hover` cards only): `0 10px 20px rgba(0,0,0,0.05)` + `translateY(-2px)`, 200ms transition.
- **No protection gradients, no scrims, no glass, no backdrop-blur.** Surfaces are flat sheets.
- **Border accent edge** (`.border-accent-edge`): 4px solid `--accent` on the header's right side in RTL (`border-right`). The system's most distinctive flourish; do not skip it on the header.

### Backgrounds & imagery

- **Background:** `#f8fafc` slate-50. No textures, no patterns, no hero images, no decorative SVG.
- **No photographic imagery in the canonical template.** The dashboard's image *is the chart itself.*
- If imagery ever enters (a printed briefing cover, an annual report), apply the **brand photo rules**: in-context (a real classroom, a real Galilee landscape), high-contrast, never stocky-warm. Wrap in a `rounded-xl border border-slate-200 shadow-sm` frame so it sits in the system.

### Animation & motion

The product is **deliberately understated.**

- **Card hover lift** — `transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.05)` — 200ms ease. The only ambient motion.
- **Chart entrance** — Chart.js default (~500ms ease-out). Don't override.
- **Tab change** — instant. No fade, no slide.
- **Filter change** — instant recompute. No skeleton, no spinner.
- **No bounce, no spring, no parallax, no reveal-on-scroll.**

### Hover & press states

- **Tab inactive → hover:** `color: slate-500 → slate-700`. No background change.
- **Tab active:** `border-bottom: 2px solid var(--accent)` + `color: var(--accent)` + `font-weight: 700`.
- **Table row hover:** `hover:bg-slate-50`. No border, no shadow.
- **Card hover:** see above.
- **Reset link hover:** `text-decoration: underline`. Color stays `var(--accent)`.
- **Buttons:** no dedicated button styling beyond reset-link and tab buttons. If a future button is needed, follow the table-search-input precedent: `border border-slate-200 rounded px-3 py-1 text-sm focus:outline-none focus:border-slate-400`.
- **Inputs (select, text):** border `slate-200`; focus border `slate-400`; **no glow ring** — the template suppresses default focus rings to keep the page calm.
- **No press states defined** for primary controls (it's not a touch app).

### Density & layout rules

- **12-column grid inside the chart area.** Charts claim `lg:col-span-4` (sm), `lg:col-span-6` (md), `lg:col-span-8` (lg), `lg:col-span-12` (full). Primary chart first and wide; secondary breakdowns smaller.
- **Sidebar is fixed-width at desktop:** `md:w-1/4`. Chart area: `md:w-3/4`. Stack vertically below `md`.
- **Tables stretch full card width** with internal horizontal scroll on overflow (`overflow-auto table-container max-h-[500px]`). Header is sticky.
- **Table virtualization:** above 500 rows, the runtime renders the first 500 + a truncation footer (`מוצגות 500 שורות ראשונות מתוך {TOTAL}`).
- **RTL inversion:** flexes still use `gap`; the `.border-accent-edge` rule swaps `border-right` / `border-left` based on `dir`. Bullet lists use `pr-5` for the marker column.
- **Nothing is fixed / sticky** at the page level (no sticky header, no FAB). Page scrolls as one document. Only the **table header** is `sticky top-0` inside its scroll container.

### Transparency & blur

- **None.** No `backdrop-filter`. No translucent overlays. Chart fills at full opacity (Chart.js defaults).
- Past dashboards in the older 03_viz style used `rgba(…, 0.7–0.8)` for chart fills; the canonical template uses solid hex from the palette. Match the canonical default for new work.

### Imagery vibe (if it ever enters)

Photographic, high-contrast, in-context. Never stock-y warm-vignette product photos. Black-and-white acceptable for editorial pages. Always frame in a slate-200 border + rounded-xl card so imagery matches the rest of the system.

---

## ICONOGRAPHY

**The canonical template ships with no icon set.** No icon font is loaded; no SVG sprite; no emoji; no Unicode symbols used as functional icons. Status, KPI identity, chart-series identity are communicated through **color (palette swatches) and Hebrew labels alone**.

The reset-filters button is plain text (`איפוס סינונים`); the table search is `placeholder="חיפוש..."` text; tabs are text-only.

### What this means in practice

- **Stay minimal.** Adding icons without need will tilt the tone toward SaaS dashboard and away from policy bulletin.
- **When icons are unavoidable** (e.g. a future export menu, a chart-card collapse toggle): use **Lucide** at **stroke-width 1.5**, `currentColor`, sized 16–20px to match body text. Lucide's understated humanist line work matches Heebo and the slate palette.
- **CDN:** `https://unpkg.com/lucide@latest`. Tag this as a flagged substitution — the brand has not formally adopted Lucide.
- **Never use:** filled/duotone icon sets (too warm), Font Awesome (busy), emoji as functional icons (off-tone), color-glyph icons.

### Logo / wordmark

The **official logo is `assets/logo.jpg`** — a bilingual lockup of the Hebrew name (מרכז ידע אזורי גליל מזרחי | מערבי) above the English name (REGIONAL KNOWLEDGE CENTER EAST | WEST GALILEE), all set in navy `#183048`, beside the pixel-mosaic mark.

- **Full logo** (`assets/logo.jpg`): use on splash pages, briefing covers, the homepage hero. Min height 80px on screen.
- **Mosaic mark alone** (`assets/mark.png`): use as the dashboard header glyph (h-14 / 56px) when the title also appears beside it. Use as a favicon. Use anywhere the wordmark is too wide.

Clear-space rule: leave at least one "tile-height" of empty space around the logo on all sides. Never recolor the mark. Never re-typeset the wordmark.

---

## ⚠️ Substitutions & flags to confirm

| Item | Status | Action |
|---|---|---|
| **Logo** | ✅ Provided — `assets/logo.jpg` + `assets/mark.png` (cropped mosaic mark) | Use directly. Source crop is JPG; an SVG version would be cleaner if available. |
| **Brand palette** | ✅ Derived from the mosaic logo — cyan + 5 mosaic-tile accents | OK as-is. |
| **Iconography** | Not used in product | Lucide @ stroke-1.5 is proposed if/when needed. Confirm or supply your own set. |
| **Fonts** | Heebo, loaded from Google Fonts CDN. Stored locally optional. | OK as-is. |
| **Accent color** | Default cyan `#18a8c0` from brand mosaic | Pick per-dashboard from the approved 6-color family or extend the list. |
| **03_viz stylistic variant** | Used Assistant font + navy + squared cards. | Canonical look is **Heebo + slate-50 + rounded-xl + cyan accent**. The 03_viz styling is one-off and should be migrated. |

## ✅ Quick start: making a new dashboard

1. Run the `excel-to-dashboard` pipeline (see `source/original_SKILL.md`) → cleaned CSV + config JSON + populated `index.html`.
2. Confirm the populated HTML imports `colors_and_type.css` and self-hosts Heebo from `fonts/`.
3. Pick a per-dashboard accent from the approved 5-color family (or default blue).
4. Write KPI labels, filter labels, chart titles using the **Voice & register** rules above. Lift from the **Verbatim copy library** where applicable.
5. Sort categoricals by measure descending, ordinals by their natural order; never alphabetize.
6. Add the privacy threshold footnote if your data was suppressed at `n<11`.
7. Run phase-4 QA (`qa_data.py` + `qa_web.py`). Fix violations at the source, not in the viz.

For full visual reference see the populated examples in `ui_kits/dashboard/` (education) and `ui_kits/demographics/` (multi-resolution).
