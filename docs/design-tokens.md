# Design tokens — sk1-hmi

Resolution: **480×272** landscape (SK1 model: `TJC4827X243_011C`).

## Colors

| Token | Hex | Use |
|-------|-----|-----|
| `bg` | `#1A1C1E` | Base charcoal background |
| `bg_elevated` | `#24272B` | Panels / bars |
| `border` | `#3A3F45` | Thin separators |
| `text` | `#F2F0EB` | Primary text |
| `text_muted` | `#9AA0A6` | Secondary / labels |
| `accent` | `#E8A838` | CTA and highlight (amber) |
| `accent_dim` | `#B07A20` | Accent pressed |
| `danger` | `#D45B4A` | Cancel / stop |
| `ok` | `#5FAF7A` | Ready / on |
| `hotend` | `#E07A5F` | Extruder |
| `bed` | `#6B9BD1` | Bed |

## Typography (HMI)

Bitmap fonts in USART HMI:

- `font_brand` — ~20–24px (SK1 name)
- `font_title` — ~16–18px page titles
- `font_body` — ~14–16px values
- `font_label` — ~12–14px labels

Avoid too many weights; prefer one clean sans family in the editor’s font generator.

## Layout

- Home: dominant brand + one status headline + two numbers (hotend/bed) + one CTA (chamber light; Print/Move/Files only in the nav).
- Other pages: title on the left, content, bottom nav bar (icons).
- No cards in the hero; panels only where there is interaction (sliders / lists).
- One job per page.

## Motion

Serial HMI does not animate like the web. Use:

1. Immediate page changes
2. Button feedback (`pic` / `pic2`)
3. Progress bar updated by the bridge (~1 Hz)
