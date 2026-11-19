# Component map (page + id → UiIntent)

Source of truth: **the real IDs stored in `hmi/sk1-hmi.HMI`**. This file is
derived from the project via `tools/hmi_dump.py`, so you can re-check anytime:

```powershell
python tools/hmi_dump.py hmi/sk1-hmi.HMI
python tools/hmi_dump.py hmi/sk1-hmi.HMI --page lights   # one page
python tools/hmi_dump.py hmi/sk1-hmi.HMI --json          # for scripts
```

Each touch arrives at the bridge as `0x65 <page> <component> <event>`; the
numbers below are exactly what the panel sends. Every touch component needs
**Send Component ID** enabled, or the panel sends nothing.

> The editor keeps the `.HMI` locked while open. Close the editor before
> dumping, or copy the file and pass the copy.

## Pages (index = `page` in the serial frame)

| Page | HMI name | Background (`pic`) | Content |
|------|----------|--------------------|---------|
| 0 | `home` | 3 | complete |
| 1 | `print` | 7 | complete |
| 2 | `move` | 5 | complete |
| 3 | `files` | 2 | complete |
| 4 | `fans` | 1 | complete |
| 5 | `lights` | 4 | **tabs + nav only** — load/unload content pending |
| 6 | `zoffset` | 9 | **nav only** — content pending |
| 7 | `calibrate` | 0 | **nav only** — content pending |
| 8 | `network` | 6 | `t_ip` (printer IP) |
| 9 | `settings` | 8 | **nav only** — content pending |

> Page 5 is named `lights` in the editor (not `load`). The bridge render path
> uses that name in `components.page_name()`.

## Bottom navigation

Shared geometry: **x/y/w/h ≈ 51 / 234 / 46 / 36** (home, print, move, files, more).

**IDs are not fixed 1..5** on every page — the editor renumbers by creation
order. The bridge uses `bridge/sk1_hmi/ui/route.py` (`_NAV`). Always verify
against `hmi/sk1-hmi.HMI.ids.json`.

| Page | nav_home | nav_print | nav_move | nav_files | nav_more |
|------|----------|-----------|----------|-----------|----------|
| home | 1 | 2 | 3 | 4 | 5 |
| print | 15 | 16 | 17 | 18 | 19 |
| move | 21 | 22 | 23 | 24 | 25 |
| files | 16 | 17 | 18 | 19 | 20 |
| fans | 11 | 12 | 13 | 14 | 15 |
| zoffset…settings | 1 | 2 | 3 | 4 | 5 |

## Page 0 — home (pic 3)

| id | Name | Type | Intent / bind |
|----|------|------|---------------|
| 6 | `b_light` | dual-state btn | `ToggleCaseLight` |
| 7 | `b_fan` | dual-state btn | `TogglePartFan` (100% / 0%) |
| 8 | `p_wifi` | picture | `NavNetwork` |
| 9 | `t_status` | text | status (bridge) |
| 10 | `t_toolhead` | text | `temperature_sensor toolboard` |
| 11 | `t_mcu` | text | `temperature_sensor mcu` |
| 12 | `t_chamber` | text | `temperature_sensor chamber` |
| 13 | `t_hotend_tgt` | text | hotend target (empty if 0) |
| 14 | `t_hotend_dir` | text | ▲ arrow (empty if target 0) |
| 15 | `t_hotend` | text | `extruder.temperature` |
| 16 | `t_bed_tgt` | text | bed target (empty if 0) |
| 17 | `t_bed_dir` | text | ▲ arrow (empty if target 0) |
| 18 | `t_bed` | text | `heater_bed.temperature` |
| 19 | `t_hotend_lbl` | hotspot | `NavMove` |
| 20 | `t_bed_lbl` | hotspot | `NavMove` |

## Page 1 — print (pic 7)

| id | Name | Type | Intent / bind |
|----|------|------|---------------|
| 1 | `j_progress` | progress | `val` = progress |
| 2 | `p_wifi` | picture | `NavNetwork` |
| 3 | `p_thumb` | picture | thumbnail |
| 4 | `b_pause` | btn | `PauseOrResume` |
| 5 | `b_cancel` | btn | `CancelPrint` |
| 6 | `t_file` | text | filename / `PAUSED` (`p0` + `title_print`) |
| 7 | `t_progress` | text | `NN%` |
| 8 | `t_hotend` | text | `actual/target` (`p1` = nozzle) |
| 9 | `t_bed` | text | `actual/target` (`p2` = bed) |
| 10–12 | `t_toolhead` `t_mcu` `t_chamber` | text | sensors |
| 13 | `t_z` | text | Z-offset |
| 14 | `t_eta` | text | ETA |
| 15–19 | `nav_*` | picture | nav (see table above) |
| 20 | `p0` | picture | print title icon |
| 21 | `b_z_m` | dual-state | `BabyStep(-0.025)` |
| 22 | `b_z_p` | dual-state | `BabyStep(+0.025)` |
| 23–24 | `p1` `p2` | picture | hotend/bed icons |

## Page 2 — move (pic 5)

| id | Name | Type | Intent |
|----|------|------|--------|
| 1 | `t_pos` | text | XYZ |
| 2 | `t_rail_hotend` | text | rail |
| 3–5 | `b_y_p` `b_z_p` `b_x_m` | dual-state | axes + |
| 6 | `b_tab_move` | dual-state | `NavMove` |
| 7–9 | `b_x_p` `b_y_m` `b_z_m` | dual-state | axes − |
| 10–11 | `b_home_xy` `b_home_z` | dual-state | home |
| 12–14 | `b_step_01` `b_step_1` `b_step_10` | dual-state | step |
| 15 | `p_wifi` | picture | `NavNetwork` |
| 16 | `b_step_30` | dual-state | step 30 |
| 17–18 | `b_tab_load` `b_tab_fan` | dual-state | tabs |
| 19–20 | `t_rail_bed` `t_rail_fan` | text | rails |
| 21–25 | `nav_*` | picture | nav |

> There is no `b_home_all` on this page: home is split across XY / Z.

## Page 3 — files (pic 2)

| id | Name | Type | Intent |
|----|------|------|--------|
| 1 | `t_title` | text | title (`p0` + `title_files`) |
| 2–6 | `t_f0`…`t_f4` | text | names |
| 7 | `p_thumb` | picture | thumb |
| 8–12 | `b_f0`…`b_f4` | dual-state | `SelectFile(0..4)` |
| 13–15 | `b_up` `b_down` `b_print` | dual-state | page / print |
| 16–20 | `nav_*` | picture | nav |
| 21 | `p0` | picture | title icon |

## Page 4 — fans (pic 1)

| id | Name | Type | Intent |
|----|------|------|--------|
| 1–3 | `b_tab_move` `b_tab_load` `b_tab_fan` | dual-state | tabs |
| 4 | `p_wifi` | picture | `NavNetwork` |
| 5–7 | `t_part` `t_side` `t_filter` | text | `%` |
| 8–10 | `h_part` `h_side` `h_filter` | slider | `Set*Fan` |
| 11–15 | `nav_*` | picture | nav |

> Sliders do not send their id in the value frame: the bridge remembers the last
> slider touched and applies the next `0x71` (NUMERIC) frame to it.

## Page 5 — lights (pic 4) — **incomplete**

| id | Name | Type | Intent |
|----|------|------|--------|
| 6 | `b_tab_move` | dual-state btn | `NavMove` |
| 7 | `b_tab_load` | dual-state btn | `NavLoad` |
| 8 | `b_tab_fan` | dual-state btn | `NavFans` |

`tc0` (touch-capture with no geometry) and leftover ids 9..14 (`t_eta`,
`t_hotend`, `t_bed`, `b_pause`, `b_cancel`, `p_thumb`) were removed in the
editor on 2026-11-18, so the page currently has only the 5 nav items + 3 tabs.

Load/unload content still needs to be created. Planned layout (see
`hmi/preview/app.js` and `bridge/sk1_hmi/ui/render.py#_load`):

| id | Name | Type | Intent |
|----|------|------|--------|
| 9 | `b_load` | dual-state btn | `LoadFilament` |
| 10 | `b_unload` | dual-state btn | `UnloadFilament` |
| 11 | `b_temp_m` | dual-state btn | `LoadTempStep(-10)` |
| 12 | `b_temp_p` | dual-state btn | `LoadTempStep(+10)` |
| — | `t_mode` `t_step1..3` | text | load progress |
| — | `t_temp_lbl` `t_set_temp` | text | temperature preset |
| — | `t_hotend` `t_hotend_tgt` | text | active temperature |
| — | `p_nozzle` `p_arrow` `p_wifi` | picture | decoration/status |

## Page 8 — network

| id | Name | Type | Intent / bind |
|----|------|------|---------------|
| 6 | `t_ip` | text | printer IP (Moonraker `/machine/system_info`) |

Opened by the **`p_wifi`** icon (home id 8, print id 2, move id 15, fans id 4) → `NavNetwork`.

Must exist on the **flashed** `.tft`. If the bridge logs `network ip=…` but the
label stays empty / commands ACK `0x1a`, recompile and reflash after adding `t_ip`
(wide enough, max length ≥ IP string).

## Pages 6 / 7 / 9 — zoffset / calibrate / settings — **incomplete**

Global nav only (settings has no extra content yet).

## How the bridge writes text

Command form `page.objname.attribute=value`, for example:

```
home.t_hotend.txt="210°C"
print.j_progress.val=42
lights.t_step1.pco=64512
```

The page name comes from `components.page_name()` — today `lights` for
`Screen.LOAD`.
