# Hebrew and RTL gotchas

Read this in full before phase 2 if the data is Hebrew. A dashboard that renders correctly in English can still be silently wrong in Hebrew because of invisible characters, inconsistent Unicode forms, and directional rendering quirks.

## Normalization

Every Hebrew string entering the pipeline must be normalized. The cleaning script does this when `normalize_hebrew: true` (which should always be true for Hebrew data).

Normalization steps, in order:
1. **Unicode NFC**. Composes base letters with combining marks into their canonical form.
2. **Strip zero-width characters**: U+200B (ZWSP), U+200C (ZWNJ), U+200D (ZWJ), U+200E (LRM), U+200F (RLM), U+202A to U+202E (explicit directional formatting), U+2066 to U+2069 (isolate controls), U+FEFF (BOM / ZWNBSP).
3. **Normalize whitespace**: collapse runs of whitespace to one space, trim. Non-breaking spaces (U+00A0) become regular spaces.
4. **Strip niqqud by default** (U+0591 to U+05C7 range: te'amim and nikud). If the user's domain keeps niqqud meaningful (religious texts, linguistics data), declare `keep_niqqud: true` in the cleaning spec.
5. **Normalize punctuation**: map geresh (U+05F3) and gershayim (U+05F4) to ASCII apostrophe and double quote only for comparison keys, not for display. Curly quotes → straight quotes for comparison.
6. **Case-fold Latin-script substrings** inside Hebrew strings (for comparison keys only, not display).

Rule of thumb: the comparison form is aggressive; the display form preserves original characters. The cleaning script produces both, stored as separate columns when needed (e.g., `city_display` and `city_key`).

## Why this matters

Without normalization, the same human-meaningful value can appear as multiple Hebrew "categories":

- `גליל עליון` vs `גליל עליון ` (trailing space)
- `קריית שמונה` vs `קרית שמונה` (different spellings; this one is a policy decision, not normalization)
- `קרית  שמונה` (double internal space)
- `קריית שמונה\u200e` (trailing LRM)
- `קריית שמונה` with niqqud marks
- `גָּלִיל עֶלְיוֹן` (with full niqqud) vs `גליל עליון`

A pivot table silently reports each of these as a separate row. A one-hot encoder silently produces one column per variant. A filter dropdown silently shows the user all of them. The dashboard lies.

Note: genuine spelling variants (`קריית` vs `קרית`) are a cleaning decision, not a normalization one. Surface them to the user as candidates for manual merge or fuzzy clustering.

## RTL and direction

- `<html lang="he" dir="rtl">` is mandatory for Hebrew dashboards.
- Tailwind's spatial utilities (`ml-*`, `mr-*`, `pl-*`, `pr-*`, `border-l-*`, `border-r-*`) have left/right semantics regardless of document direction. Prefer logical-property alternatives where available (`ms-*`, `me-*`, `ps-*`, `pe-*` with Tailwind's logical-property plugin), or accept that in RTL, `border-r` visually renders on the left. The sample template mixes both; that is OK but be aware when debugging layout.
- Numbers render left-to-right inside Hebrew RTL text by default, which is correct. Dates can render ambiguously; the template formats dates explicitly with `Intl.DateTimeFormat('he-IL')` so the order is unambiguous.
- English proper nouns inside Hebrew text (e.g., "עבד ב־Microsoft") render correctly when no explicit bidi override is needed, but if the string is very short or starts with punctuation, wrap in `<bdi>` or `<span dir="ltr">` for safety.

## Fonts

Heebo is the default. It covers Hebrew, Latin, numbers, and common punctuation. Alternatives:
- **Rubik**: similar character set, rounder feel. Also on Google Fonts.
- **Assistant**: narrower.
- **David Libre**: serif, for editorial-style dashboards.

Do not use pure Latin-script fonts (Inter, Helvetica, etc.) as primary. They will fall back to the browser's default Hebrew, which varies wildly.

## Chart axis labels in Hebrew

Chart.js by default treats axis-label strings as opaque. Hebrew labels render correctly. What can go wrong:

- **Rotated labels** become visually unreadable in RTL because Chart.js rotates around the baseline and the text can appear upside-down-right-to-left. Prefer horizontal bars for long Hebrew labels.
- **Truncation with ellipsis** in Chart.js uses `...` by default, which renders on the wrong side in RTL. Use the Unicode character `…` (U+2026) and wrap the label with an explicit `\u200F` (RLM) to anchor direction.
- **Mixed-direction labels** (e.g., "שכר ₪") benefit from `direction: 'rtl'` in the Chart.js font config.

## Search in the data table

String search on Hebrew needs the same normalization as the data. The template's table-search runs `normalizeHe(value)` before comparing. If a user's search query is "קריית" and the cell is "קריית שמונה\u200e", the raw comparison fails; normalized comparison succeeds. The runtime JS includes a small normalizer function that matches the Python cleaning logic.

## Sorting

JavaScript's default string sort on Hebrew is undefined by spec and varies by engine. Hebrew collation via `Intl.Collator('he', {...})` is more consistent but still has quirks (the letters with final forms sort differently in different strengths).

For dashboards: never sort by Hebrew strings on chart axes. Sort by the numeric measure. In tables, use `Intl.Collator('he')` with `sensitivity: 'base'` for a consistent (if not perfect) Hebrew sort, which is what the runtime's table sort does.

## Export and copy

Users copy from dashboards. Copying normalized text back into another system can confuse them if the copy differs from the displayed form. The template keeps the display form in the rendered DOM and the normalized form in `data-*` attributes for search and sort.

## Common mistakes to avoid

- Stripping niqqud from a dataset where niqqud is semantic (biblical, liturgical, educational).
- Treating `ך` (final kaf) and `כ` (medial kaf) as the same for comparison. They are different Unicode code points and, in Hebrew orthography, always represent the same phoneme but the distinction is positional. Normalization does not equate them and should not; normalization equates visually-identical forms, not orthographically-equivalent ones.
- Forgetting to set `dir="rtl"` on nested HTML generated at runtime. The runtime's chart builders inherit direction from `<html>`, but some Chart.js plugins inject DOM elements at the `<body>` root that may not inherit as expected.
- Assuming `<input dir="auto">` does the right thing for search boxes. It does for user input, but only if the user types Hebrew. Set `dir="rtl"` explicitly on search boxes in Hebrew dashboards.
- Truncating Hebrew strings by byte count instead of grapheme count. Hebrew code points are 2 bytes in UTF-8 for the main block, and combining marks add more. Use Intl.Segmenter or grapheme-aware libraries.

## Testing

Hebrew test strings worth including in fixtures:
- Plain: `גליל עליון`
- With niqqud: `גָּלִיל עֶלְיוֹן`
- With LRM: `גליל עליון\u200e`
- Double space: `גליל  עליון`
- Trailing space: `גליל עליון `
- With Latin: `Microsoft בע״מ`
- With digits: `דירוג 7 לפי הלמ״ס`
- With quotes: `מועצה מקומית "אזורית"` (both curly and straight)

After normalization, the first five should produce the same key.
