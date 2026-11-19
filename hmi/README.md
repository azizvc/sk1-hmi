# HMI project (USART HMI)

The binary `.HMI` / `.tft` is produced in the graphical editor. This directory holds the **spec**, assets, and checklist so IDs stay aligned with the bridge.

## Correct editor

| Panel | Editor |
|-------|--------|
| TJC (SK1 stock) | **USART HMI** — http://wiki.tjc1688.com/download/usart_hmi.html |
| Genuine Nextion / prototype | Nextion Editor (prototype only) |

On the SK1, use USART HMI with the **model printed on the panel label**.

## Create the project (checklist)

1. New project → model **`TJC4827X243_011C`** → **landscape 0°** → **480×272**.
2. `Program.s` / config: baud **115200**, brightness 100.
3. Create fonts (`font_brand`, `font_title`, `font_body`, `font_label`).
4. Import backgrounds from `../assets/backgrounds/` and icons from `../assets/icons/`.
5. Create pages `home`…`settings` (IDs 0–9) per [../docs/component-map.md](../docs/component-map.md).
6. On **every button**: Touch Release → **Send Component ID**.
7. Compile → copy `.tft` to `export/sk1-hmi.tft`.

More detail: [BUILD.md](BUILD.md).

## Generate backgrounds

```bash
python tools/generate_assets.py
```

## Simulator / bench

Use the USART HMI debugger with the bridge pointed at a PC COM port (USB-TTL), or run the bridge with `dry_run = true`.

Browser layout preview: [preview/index.html](preview/index.html).
