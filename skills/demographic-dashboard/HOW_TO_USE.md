# How to use this design system with an AI agent

This folder is a **design system** for the Eastern Galilee Knowledge Center. It lets any AI agent build a new BI dashboard that automatically looks and behaves like the Center's existing dashboards: Hebrew RTL, brand colors from the logo, drill-down filters, weighted aggregation, the right chart types.

You don't need to explain the brand to the agent every time. You point it at this folder and it reads the rules itself.

---

## Step 1 — give the agent the files

Pick whichever matches your setup:

- **Agent inside this same project** (the one you're in now): no setup. Just write the prompt in Step 2.
- **Claude Code / an agent with a file system**: download this project as a folder (your designer can package it for you), and drop it into the agent's working directory. The `SKILL.md` at the root makes it an invocable skill named **`egkc-design`** — the agent can load it on demand.
- **A different chat / tool**: upload the whole folder (or at least `README.md`, `SKILL.md`, `colors_and_type.css`, and the `ui_kits/` you want to start from).

---

## Step 2 — the prompt to give your agent

Copy this, fill in the three bracketed lines at the bottom, and send it:

```
Use the Eastern Galilee Knowledge Center design system in this folder.

1. Read README.md (especially the sections "Data resolution model",
   "Content fundamentals", and "Visual foundations") and SKILL.md
   (especially "Data robustness — handle any input").

2. Copy ui_kits/demographics/ as your starting point — it already has the
   drill-down filter cascade, weighted aggregation, brand chrome, and design
   tokens wired up. (Use ui_kits/dashboard/ instead if my data is a simple
   single-metric comparison rather than nested geographic data.)

3. Replace data.js with my cleaned data, keeping the nesting columns
   (cluster / authority / settlement, or whatever levels my data has).

4. Keep these rules NON-NEGOTIABLE:
   - Hebrew, right-to-left (dir="rtl"), Heebo font
   - slate-50 background, white rounded-xl cards, shadow-sm
   - Import colors_and_type.css and use the brand accent (default = cyan)
   - Aggregate-by-default, with drill-down on demand
   - Weight all aggregations by population/count — never average the averages
   - Civic-formal tone: no emoji, no exclamation marks, no em-dashes
   - Add the privacy footnote if any rows were suppressed for low counts

MY DATA: [attach the file, or describe the columns]
THE QUESTION IT SHOULD ANSWER: [one sentence]
TOPIC / ACCENT: [tourism → gold, welfare → magenta, education → blue,
                 demographics → blue, general → cyan]
```

---

## Step 3 — the two things that decide whether it comes out right

### 1. Give it the *question*, not just the data
The single most useful line is **"what question should this dashboard answer, in one sentence?"** That's what tells the agent which charts to build. "Compare matriculation results across my towns vs. the national average" produces a very different dashboard than "show the age structure of each town." Same data, different question, different design.

### 2. Clean the data first (or tell the agent to)
See the next section — this is the #1 reason dashboards come out broken.

---

## What "clean the data first" means

Government Excel files are almost never ready to plug into a dashboard as-is. "Cleaning" means fixing the data **before** it becomes a chart, so the numbers are trustworthy and the agent doesn't have to guess. In practice it means:

| Problem in raw Excel | What it looks like | What cleaning does |
|---|---|---|
| **Merged / multi-row headers** | The title row spans 3 rows; columns have no single clear name | Flatten to one header row with clear column names |
| **Hebrew quirks** | Straight quotes instead of gershayim (`אטי"ב` vs `אטי״ב`), trailing spaces, mixed RTL/LTR | Normalize text so the same town isn't counted as two |
| **Zero-as-missing** | A kibbutz shows `wage: 0` when it really means "not reported" | Mark these as missing, so they don't drag the average to zero |
| **Mixed types** | A number column has `"1,234"`, `"N/A"`, `"<11"`, blanks | Convert to real numbers; handle the suppressed/blank cases |
| **Suppressed small counts** | Rows hidden because fewer than 11 people | Keep the rule and show the privacy footnote, don't fabricate |
| **Inconsistent names** | "קרית שמונה" vs "קריית שמונה" for the same town | Standardize so filters and joins work |
| **Stray typos in keys** | An actual one we found: a column named `haredi_pctדד` | Coerce/ignore the noise so it doesn't crash |

**Why it matters:** if you feed a dashboard dirty data, the totals will be wrong, the same town will appear twice in a filter, averages will be skewed by fake zeros, and charts will silently drop rows. The dashboard *looks* fine but the numbers lie.

**Your two options:**

1. **Clean it yourself first** — get the file into a tidy table (one header row, one row per place, real numbers, consistent names) before handing it over. Excel/Sheets is fine for this.

2. **Tell the agent to clean it** — say *"audit and clean this data before building — it's a raw government Excel export, expect Hebrew encoding issues, merged headers, and zeros that mean 'missing'."* The `source/` folder in this project contains the cleaning references the agent can follow (`hebrew_gotchas.md` and the phase documents). This is the easier path, just be explicit that the file is raw.

Either way: **don't skip it.** A clean table in, a trustworthy dashboard out.

---

## Quick reference — what's in this folder

| File / folder | Use it for |
|---|---|
| `README.md` | The full rulebook: brand, content tone, colors, type, data-resolution model |
| `SKILL.md` | The agent's entry point + the 7 data-robustness rules |
| `colors_and_type.css` | The design tokens — every dashboard imports this |
| `ui_kits/demographics/` | **Best starting point** for nested geographic data (village → authority → cluster) |
| `ui_kits/dashboard/` | Starting point for single-metric comparisons (e.g. one score vs. benchmarks) |
| `assets/` | The logo and brand mark |
| `preview/` | Small visual examples of every component and color |
| `source/` | The original dashboards + data-cleaning references |
