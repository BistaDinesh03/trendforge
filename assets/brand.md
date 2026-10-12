# TrendForge visual identity

Single source of truth for colors, geometry, and asset usage. TrendForge and
ForgeFix share the same mark system: same hexagon, same weight, different
interior idea. Keep every surface (README, docs, social) consistent with
this file.

## Shared grid and geometry

| Property | Value |
| --- | --- |
| Canvas | 24x24 units (`viewBox="0 0 24 24"`) |
| Container | pointy-top hexagon, radius 10.5, centered (12, 12) |
| Corner radius | 2 units on the hexagon vertices |
| Interior cut | stroke width 4, round caps, round joins |
| Style | flat, monoline interior, no gradients, no shadows |

The mark is a filled hexagon with the interior knocked out (SVG `<mask>`).
TrendForge's interior is a **rising sparkline with a node at the peak**: a
zigzag that ends higher than it started, terminated by a circle — "trending
upward" in one shape.

Radius note: the 4-unit design radius is for rectangular elements. On the
hexagon it is 2 units — a 4-unit radius consumes 44% of each 10.5-unit edge
and turns the silhouette into a blob at 16px.

### Shared hexagon path (identical in both repos)

```
M13 2.077 L20.093 6.173 A2 2 0 0 1 21.093 7.905 L21.093 16.095
A2 2 0 0 1 20.093 17.827 L13 21.923 A2 2 0 0 1 11 21.923 L3.907 17.827
A2 2 0 0 1 2.907 16.095 L2.907 7.905 A2 2 0 0 1 3.907 6.173 L11 2.077
A2 2 0 0 1 13 2.077 Z
```

### TrendForge cut path

```
M7.8 15.2 L11.6 11.4 L14 13.8 L16.2 11.1   (stroke 4, round caps)
circle cx=16.2 cy=11.1 r=3.4                (node at the peak)
```

Minimum clearance to the hexagon boundary: 1.49 units — at the 1.4-unit
floor that keeps gaps at about one rendered pixel when the mark is 16px.

## Color palette

| Token | Hex | Use |
| --- | --- | --- |
| Primary light | `#0F172A` | Text and mark on light surfaces |
| Accent light | `#2563EB` | Links, `logo.png` mark |
| Success light | `#16A34A` | Passing checks in docs |
| Muted light | `#475569` | Banner tagline on light |
| Subtle light | `#94A3B8` | Banner URL, secondary text |
| Primary dark | `#F8FAFC` | Text and mark on dark surfaces |
| Accent dark | `#60A5FA` | Links on dark |
| Success dark | `#22C55E` | Passing checks on dark |

Rules: flat fills only, no gradients, no shadows, at most one accent color
per surface.

### Measured contrast (WCAG 2.1)

| Pair | Ratio |
| --- | --- |
| `#0F172A` mark on `#FFFFFF` | 17.85:1 |
| `#F8FAFC` mark on `#0F172A` | 17.06:1 |
| `#2563EB` on `#FFFFFF` | 5.17:1 |
| `#475569` tagline on `#FFFFFF` | 7.58:1 |
| `#94A3B8` on `#0F172A` | 6.96:1 |
| `#94A3B8` URL on `#FFFFFF` | 2.56:1 (spec-mandated color) |

Run `python scripts/validate_assets.py` to re-print these numbers.

## Typography

SVG and banner text use the system stack only:

```
system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
```

No embedded web fonts. Rasters use Segoe UI (the Windows system font in the
same stack). Hierarchy comes from spacing, weight, and size.

## Assets

| File | Dimensions | Purpose |
| --- | --- | --- |
| `logo.svg` | 24x24 viewBox | Primary mark, `currentColor` |
| `logo-dark.svg` | 24x24 viewBox | Mark on dark surfaces |
| `logo-mono.svg` | 24x24 viewBox | Single-color mark (`#0F172A`) |
| `favicon.svg` | 32x32 viewBox | Hexagon + rising line, simplified |
| `logo.png` | 512x512 | Raster mark, accent blue, transparent |
| `banner.svg` | 1280x320 | README hero, transparent, dark text |
| `banner-dark.svg` | 1280x320 | README hero, transparent, light text |
| `social-preview.svg` | 1280x640 | Social card source |
| `social-preview.png` | 1280x640 | Social card, opaque `#0F172A` |

Every SVG is self-contained: no external references, no network fonts, under
50 KB, `<title>` present. PNGs are under 200 KB.

## Banner grid math

Composition (both banners, exact):

```
horizontal   64 margin + 96 mark + 24 gap = 184 text start x
vertical    112 top + 96 mark + 112 bottom = 320 canvas
mark box    x=64, y=112, 96x96 (24-unit mark scaled 4x)
wordmark    x=184, baseline 160 (= mark vertical center 112 + 48)
            size 64, weight 700, letter-spacing -1
tagline     x=184, baseline 200 (below wordmark, no overlap), size 22
URL         end-anchored x=1216, baseline 256 (= 320 - 64), size 16
```

Social preview: opaque `#0F172A` canvas; mark 120x120 centered at (580, 96);
wordmark centered baseline 304, tagline baseline 352, URL baseline 568.

## Regenerating rasters

The SVGs are the source of truth. On a machine with the usual SVG tools:

```bash
rsvg-convert -w 512 -h 512 assets/logo.svg -o assets/logo.png
inkscape assets/logo.svg --export-png=assets/logo.png -w 512
```

Note: both need `currentColor` resolved first (the PNG is accent blue).
This repo's authoring machine has neither tool, so the committed rasters
are produced by the Pillow renderer that mirrors the same coordinates:

```bash
python assets/render_rasters.py
```

It draws at 4x and downsamples, and asserts dimensions, alpha, and the
200 KB limit.

## Validation

```bash
python scripts/validate_assets.py
```

Checks XML well-formedness, `<title>`, size limits, no external refs,
viewBox bounds, the shared hexagon, banner grid numbers, PNG properties,
and contrast ratios. CI does not run it; run it before opening a PR that
touches `assets/`.

## Rules for new assets

1. Reuse the 24-unit grid, the shared hexagon path, and the palette above.
2. Draw by hand. No AI image generators, no raster tracing, no third-party
   icon sets (CC0/MIT/ISC only, with attribution in this file).
3. Flat and monoline. No gradients, no shadows, no isometric tricks.
4. Text in SVGs is real `<text>`, and `font-family` ends in `sans-serif`.
5. Keep the sibling rule: same hexagon, same weight, different interior.
6. Re-run the validator and regenerate rasters.

## Licensing

All assets in this directory are original work, MIT licensed with the rest
of the repository (see `LICENSE`). No third-party icons are embedded.
