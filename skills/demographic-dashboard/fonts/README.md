# Fonts

This folder is where **self-hosted Heebo .woff2 files** live for offline use, print exports, and consistent rendering when CDN access isn't available.

## Current behaviour

By default, `colors_and_type.css` loads Heebo from **Google Fonts CDN**:

```css
@import url("https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;900&display=swap");
```

This is the same source the canonical template uses, and it's licensed OFL through Google Fonts. No action required for online dashboards.

## Going offline / for print

1. Download the 5 weights from <https://fonts.google.com/specimen/Heebo> (or a TTF→woff2 conversion).
2. Drop these files into this folder:
   - `Heebo-Light.woff2` (300)
   - `Heebo-Regular.woff2` (400)
   - `Heebo-Medium.woff2` (500)
   - `Heebo-Bold.woff2` (700)
   - `Heebo-Black.woff2` (900)
3. Uncomment the `@font-face` block in `colors_and_type.css` (it's already prepared, just commented out).
4. Comment out the `@import url(…)` line above it.

## License

Heebo is licensed under the **SIL Open Font License 1.1**. Free to use, embed, and bundle commercially. Designers: Oded Ezer (Hebrew), Christian Robertson (Latin glyphs from Roboto).

## Why Heebo and not Assistant?

The canonical template (`source/canonical_template.html`) declares Heebo. The 03_viz example used Assistant — that was a one-off variant. New dashboards should use Heebo to stay in the family.
