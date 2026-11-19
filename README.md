# sk1-hmi

Open replacement HMI for the **TwoTrees SK1** stock TJC touchscreen, plus a Python bridge to modern **Moonraker / Klipper**.

It replaces the proprietary `mksclient`. The panel speaks UART; the bridge speaks WebSocket/HTTP to Moonraker.

> **Status:** usable core (home, print, move, files, fans, Wi‑Fi → network IP). Load/unload, z-offset, calibrate, and settings pages are still incomplete. Expect to flash a matching `.tft` whenever UI objects change.

---

## Why this exists

Stock SK1 UI is tied to Makerbase’s closed client. This project keeps the same panel hardware and drives it with:

1. A **USART HMI** project (`.HMI` → `.tft`) built for the exact SK1 model  
2. A small **Python bridge** that maps touch IDs → intents → Moonraker/gcode and paints the screen

---

## Hardware

| Item | Value |
|------|--------|
| Panel | **TJC4827X243_011** / `011C` |
| Resolution | **480×272** landscape |
| UART | **115200** 8N1, **3.3 V TTL** data |
| Power | **5 V** to the panel (capable supply) |
| On SK1 | typically `/dev/ttyS1` |

**Do not** flash a Nextion `NX8048…` / 800×480 project — the panel rejects it (`Model does not match`).

**Do not** put 5 V on RX/TX. Common GND is required.

Details: [docs/wiring.md](docs/wiring.md)

---

## Architecture

```
┌─────────────┐   UART 115200   ┌──────────────────┐   WS/HTTP   ┌───────────┐
│ TJC panel   │ ◄─────────────► │ sk1-hmi bridge   │ ◄─────────► │ Moonraker │
│ (sk1-hmi.tft)│  touch + cmds  │ (Python service) │             │ + Klipper │
└─────────────┘                 └──────────────────┘             └───────────┘
```

- Touch frames: `Send Component ID` → `(page, component)` → `bridge/sk1_hmi/ui/route.py`  
- Screen updates: `bridge/sk1_hmi/ui/render.py` (named objects, e.g. `home.t_hotend.txt="210°C"`)  
- **Never** send Nextion-style `vis` — USART ACKs `0x1a` and floods the link

---

## Repository layout

| Path | Purpose |
|------|---------|
| `hmi/` | USART HMI project (`sk1-hmi.HMI`), images, preview, exported `.tft` |
| `bridge/` | Python package `sk1_hmi` (serial, Moonraker, state, render) |
| `docs/` | Component map, deploy, flash, wiring, design tokens |
| `assets/` | Backgrounds / icons used by the HMI |
| `packaging/` | systemd unit, example config, helper scripts |
| `tools/` | `hmi_dump.py`, asset generators, editor helpers |

---

## Quick start (development)

```bash
cd bridge
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m sk1_hmi --config ../packaging/config.example.toml
```

Set `dry_run = true` in the config to exercise logic without a serial port. Point `serial` at your USB‑TTL adapter (e.g. `COM3` / `/dev/ttyUSB0`) for a bench panel.

Browser preview (layout only): open [`hmi/preview/index.html`](hmi/preview/index.html).

Tests:

```bash
cd bridge
pip install pytest
PYTHONPATH=. pytest -q
# Windows PowerShell: $env:PYTHONPATH="."; pytest -q
```

---

## Building the HMI (`.tft`)

**Editor:** [USART HMI](http://wiki.tjc1688.com/download/usart_hmi.html) only for production flashes.

1. Open `hmi/sk1-hmi.HMI` in USART HMI  
2. Model must be **TJC4827X243_011**, **480×272**, encoding **utf-8**, baud **115200**  
3. Every button/hotspot: Touch Release → **Send Component ID**  
4. **Compile**, then copy the output `.tft` to `hmi/export/sk1-hmi.tft`  
5. Flash the panel (see below)

Full notes: [hmi/BUILD.md](hmi/BUILD.md) · IDs: [docs/component-map.md](docs/component-map.md)

### Important constraints

- **Edit the UI only in USART HMI.** Patching the `.HMI` binary by script breaks checksums (`Version mismatch`).  
- The editor locks the project file while open; close it before `Copy-Item` / dump tools.  
- After adding or renaming objects (e.g. `network.t_ip`), you **must recompile and reflash**. The bridge cannot invent components the panel firmware does not have — commands return ACK `0x1a`.  
- Text fields need enough **width** and **max length** for the longest string (e.g. seed `t_ip` with `000.000.000.000`).  
- Keep `hmi/sk1-hmi.HMI.ids.json` in sync (`python tools/hmi_dump.py hmi/sk1-hmi.HMI --snapshot`) so `route.py` matches real IDs.

---

## Flash the panel

1. Backup stock `LKS.tft`  
2. FAT32 microSD, single `.tft` in the root  
3. Power off → insert SD → power on → wait for update finished  
4. Power off → remove SD → reassemble  

Guide: [docs/flash-tft.md](docs/flash-tft.md)

---

## Install on the printer

Only one process may own `/dev/ttyS1`. Disable `mksclient` first, then install the bridge as a systemd service.

```bash
# high-level — see docs/deploy.md for the full sequence
sudo mkdir -p /opt/sk1-hmi /etc/sk1-hmi
# copy bridge + deps, install packaging/sk1-hmi.service
sudo systemctl enable --now sk1-hmi
sudo journalctl -u sk1-hmi -f
```

Config: `/etc/sk1-hmi/config.toml` (start from [`packaging/config.example.toml`](packaging/config.example.toml)).

Full guide: [docs/deploy.md](docs/deploy.md)

### Smoke checklist

- [ ] Home shows live temps  
- [ ] Nav between home / print / move / files  
- [ ] Wi‑Fi icon → **network** page shows IP in `t_ip`  
- [ ] Pause / resume during a print  
- [ ] Case light / part fan toggles  
- [ ] Move blocked while printing  
- [ ] Service restarts after kill  

---

## Open-source roadmap

This repo is being prepared for public release. Before tagging `v0.1`:

| Task | Notes |
|------|--------|
| License | **MIT** — see root [`LICENSE`](LICENSE) |
| Keep LICENSE current | Update copyright year/holders as needed |
| Scrub secrets | No printer IPs, passwords, or private paths in docs/scripts (use examples) |
| Pin a release `.tft` | Ship `hmi/export/sk1-hmi.tft` that matches the documented ID map |
| CI | `pytest` on `bridge/` for PRs |
| Issue templates | Bug = panel model + baud + `journalctl` snippet + whether `.tft` was reflashed |
| Code of conduct | Optional but recommended for community forks |

### Contributing (draft)

1. Prefer small PRs: bridge logic **or** HMI assets/docs, not both unless required.  
2. If you change touch IDs or object names, update `docs/component-map.md`, `route.py`, and regenerate `hmi/sk1-hmi.HMI.ids.json`.  
3. Do not commit `_deploy_stage/`, local passwords, or editor installers.  
4. Conventional commits welcome: `feat:`, `fix:`, `docs:`, `chore:`.  
5. Test on real hardware when touching serial/render paths; `0x1a` ACKs usually mean “object missing on flashed TFT” or invalid instruction.

---

## Safety & disclaimer

- Back up `printer.cfg`, `moonraker.conf`, eMMC image, and stock `LKS.tft` before deploying.  
- Wrong wiring can damage the panel or SoC.  
- This project is **not** affiliated with TwoTrees or Makerbase. Use at your own risk; it can move axes and heat heaters via Klipper.

---

## Documentation index

| Doc | Content |
|-----|---------|
| [hmi/BUILD.md](hmi/BUILD.md) | USART project build / export |
| [docs/component-map.md](docs/component-map.md) | Page & component IDs ↔ intents |
| [docs/deploy.md](docs/deploy.md) | Install on SK1 |
| [docs/flash-tft.md](docs/flash-tft.md) | microSD flash |
| [docs/wiring.md](docs/wiring.md) | UART / power |
| [docs/design-tokens.md](docs/design-tokens.md) | Visual language |
| [docs/editors.md](docs/editors.md) | USART vs Nextion |

---

## License

Released under the [MIT License](LICENSE).

USART HMI / TJC editor tooling remain under their vendors’ terms; this repository does not redistribute those installers.
