# Building the HMI skeleton

## Editor

**USART HMI** (the only toolchain that flashes this panel correctly).

Project file: `hmi/sk1-hmi.HMI`

- Model **`TJC4827X243_011`** · **480×272** landscape · encoding **`utf-8`**
- Baud **115200** (USART + bridge)
- Nextion Editor may be installed for experiments, but its `.HMI` format is
  **different** and must not be used for SK1 production flashes.

> An older Nextion project targeting `NX8048T070_011` does **not** flash on this
> panel — error `Model does not match / File Info ERROR!`. Do not use it.

## Current project state

- 10 pages: `home` … `settings`
- Backgrounds via `sta=image` + `pic`
- Home / print / move / files / fans are built out; `lights` has tabs + nav
  (load/unload content pending); `zoffset` / `calibrate` / `settings` are
  nav-only; `network` has `t_ip` for the printer IP. IDs: [`docs/component-map.md`](../docs/component-map.md).

## Export `hmi/export/sk1-hmi.tft`

Click **Compile** (toolbar icon). USART HMI writes the binary under:

`%AppData%\USART HMI\work\a-<timestamp>\output\sk1-hmi.tft`

Copy that file to `hmi/export/sk1-hmi.tft`.

Flash on the TJC: microSD bootloader (see [`docs/flash-tft.md`](../docs/flash-tft.md)) or Upload from the editor.

## Checking IDs without guessing

The editor keeps the `.HMI` open exclusively, so `Copy-Item` fails while it runs. Two options:

```powershell
# 1) editor CLOSED — dump + snapshot for tests / CI
python tools/hmi_dump.py hmi/sk1-hmi.HMI --snapshot
python tools/hmi_page.py hmi/sk1-hmi.HMI 5     # one page, via entry table

# 2) editor open — use the previous snapshot
bridge\.venv\Scripts\python.exe -m pytest bridge -q
```

> **Format trap:** the `.HMI` is an entry table (`u32` count +
> `count × 28` bytes: `char name[16]`, `u32 offset`, `u32 size`, `u32 tag`) with
> payloads from `0x700000`. Each save **appends** new payloads and leaves old
> ones as orphaned junk in the same file. A linear blob scan finds objects that
> were already deleted in the editor — `hmi_dump.py` reads the entry table to
> avoid that.
>
> Writing the `.HMI` by script **does not work**: undocumented checksums make
> the editor reject the file with *"Version mismatch"*. All UI edits must go
> through the GUI.

## UI checklist

1. Import `assets/backgrounds/*.png` and `assets/icons/*.png` (also under `hmi/images/`).
2. Pages = names from `pages/pages.json`.
3. Components = [`docs/component-map.md`](../docs/component-map.md).
4. On every button/hotspot: Touch Release → **Send Component ID**.
5. Compile + Upload → copy the resulting `.tft` to `hmi/export/sk1-hmi.tft`.
6. After adding text objects (e.g. `t_ip`), give them enough **width** and **max length**, then **reflash** — the bridge cannot update components missing from the panel firmware (ACK `0x1a`).
