# Design

## Direction

Swiss transit signage. A public timetable is dense, legible, unornamented, and has one job: get you
from a link to a file. The interface borrows that discipline. Paper, ink, hairlines, one signal
colour, zero radius, tabular numerals.

## Tokens

| Token | Value | Use |
| --- | --- | --- |
| paper | `#F4F3EF` | page |
| card | `#FBFAF7` | fields, panels |
| ink | `#131311` | text, borders |
| rule | `#DCDAD2` | hairlines |
| muted | `#6B6B63` | secondary text |
| signal | `#002FA7` | primary action, active tab, focus ring |

One accent. It never appears as decoration, only as state or action: the Fetch block, the active
tab, the progress line, the focus ring, the wordmark period.

## Type

- **Archivo** variable, width axis at 112 for display and 118 for the wordmark. One family for the
  whole page, hierarchy from weight and width rather than from a second typeface.
- **Geist Mono** for anything numeric: sizes, durations, format ids, bitrates, domains.
- Display sizes: hero `clamp(1.9rem, 3.6vw, 2.85rem)`, result title `2rem` to `2.25rem`, section
  body `15px`, table `12px` to `14px`.

## Layout

- Max width 1400, gutters 20/32.
- Hero is a two-column block: message and field on the left (max 820), a quiet extractor list on the
  right (260) that proves the 1,751 claim with real names. It disappears once a result is loaded.
- Result is `1.5fr / 1fr`: preview, facts and the format workspace on the left, metadata and the
  primary download on a sticky rail at the right.
- Structural devices are information: the rule above the extractor list, the rule between table
  rows, the rule under the tabs. Nothing is decorative.

## Motion

Two moments only.

1. An indeterminate 1px signal line while a probe runs. It reports work, so it moves.
2. Hover and active states on rows and buttons, 120ms, transform or background only.

No scroll reveals, no parallax, no marquee. `prefers-reduced-motion` collapses everything.

## Rules that held during the build

- No em-dashes in copy.
- No eyebrow labels above sections.
- No three-card feature row, no gradient hero, no glassmorphism.
- Table rows are hairlines, not cards.
- Empty, loading and error states are all designed: an empty field focuses itself, a bad link shows
  an inline rule-marked message, a missing preview shows cover art instead of a black box.

## Known limitations

The player is only as good as the source. Chromium builds without proprietary codecs will not decode
H.264 or AAC, so the preview area can look blank in headless environments even when the bytes are
flowing correctly. Verify playback in a normal browser.
