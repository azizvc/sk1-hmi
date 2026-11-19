from __future__ import annotations

from ..app.state import AppState, PrintState, Screen
from .components import (
    MOVE_STEP_OBJS,
    MOVE_STEP_PICS,
    PIC_FAN_OFF,
    PIC_FAN_ON,
    PIC_LIGHT_OFF,
    PIC_LIGHT_ON,
    dim,
    page,
    page_name,
    pic,
    txt,
    val,
)


def render_full(state: AppState) -> list[str]:
    cmds = [page(state.ui.screen.value), dim(state.ui.brightness)]
    cmds.extend(_render_screen(state, full=True))
    return cmds


def render_diff(old: AppState, new: AppState) -> list[str]:
    cmds: list[str] = []
    if old.ui.screen != new.ui.screen:
        return render_full(new)
    if old.ui.brightness != new.ui.brightness:
        cmds.append(dim(new.ui.brightness))
    cmds.extend(_render_screen(new, full=False, old=old))
    return cmds


def _render_screen(state: AppState, *, full: bool, old: AppState | None = None) -> list[str]:
    p = page_name(state.ui.screen)
    if state.ui.screen == Screen.HOME:
        return _home(p, state, full, old)
    if state.ui.screen == Screen.PRINT:
        return _print(p, state, full, old)
    if state.ui.screen == Screen.MOVE:
        return _move(p, state, full, old)
    if state.ui.screen == Screen.FILES:
        return _files(p, state, full, old)
    if state.ui.screen == Screen.FANS:
        return _fans(p, state, full, old)
    if state.ui.screen == Screen.LOAD:
        return _load(p, state, full, old)
    if state.ui.screen == Screen.ZOFFSET:
        return _zoffset(p, state, full, old)
    if state.ui.screen == Screen.CALIBRATE:
        return _calibrate(p, state, full, old)
    if state.ui.screen == Screen.NETWORK:
        return _network(p, state, full, old)
    if state.ui.screen == Screen.SETTINGS:
        return _settings(p, state, full, old)
    return []


def _changed(full: bool, old: AppState | None, getter) -> bool:
    if full or old is None:
        return True
    return getter(old) != getter


def _fmt_sensor(val: float | None) -> str:
    return f"{val:.0f}°C" if val is not None else "--°C"


def _home_temp_snapshot(s: AppState) -> tuple[str, ...]:
    """Display strings only — ignores float jitter that would flood UART paints."""
    hot_on = s.temps.hotend_target > 0
    bed_on = s.temps.bed_target > 0
    return (
        f"{s.temps.hotend:.0f}°C",
        f"{s.temps.hotend_target:.0f}°C" if hot_on else "",
        "▲" if hot_on else "",
        f"{s.temps.bed:.0f}°C",
        f"{s.temps.bed_target:.0f}°C" if bed_on else "",
        "▲" if bed_on else "",
        _fmt_sensor(s.temps.toolhead),
        _fmt_sensor(s.temps.mcu),
        _fmt_sensor(s.temps.chamber),
    )


def _home(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    cmds: list[str] = []
    if full or not old or old.ui.status_text != s.ui.status_text:
        cmds.append(txt(p, "t_status", s.ui.status_text))
    # USART rejects Nextion-style `vis` (ACK 0x1a flood) — hide targets via empty txt.
    new_lbl = _home_temp_snapshot(s)
    old_lbl = _home_temp_snapshot(old) if old else None
    if full or old_lbl != new_lbl:
        hot, hot_tgt, hot_dir, bed, bed_tgt, bed_dir, tool, mcu, chamber = new_lbl
        cmds += [
            txt(p, "t_hotend", hot),
            txt(p, "t_hotend_tgt", hot_tgt),
            txt(p, "t_hotend_dir", hot_dir),
            txt(p, "t_bed", bed),
            txt(p, "t_bed_tgt", bed_tgt),
            txt(p, "t_bed_dir", bed_dir),
            txt(p, "t_toolhead", tool),
            txt(p, "t_mcu", mcu),
            txt(p, "t_chamber", chamber),
        ]
    if full or not old or old.lights.case_light != s.lights.case_light:
        cmds.append(pic(p, "b_light", PIC_LIGHT_ON if s.lights.case_light else PIC_LIGHT_OFF))
    if full or not old or (old.fans.part >= 50) != (s.fans.part >= 50):
        cmds.append(pic(p, "b_fan", PIC_FAN_ON if s.fans.part >= 50 else PIC_FAN_OFF))
    return cmds


def _print(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    cmds: list[str] = []
    file_label = _print_file_label(s)
    if full or not old or _print_file_label(old) != file_label:
        cmds.append(txt(p, "t_file", file_label))
    if full or not old or old.print.progress != s.print.progress:
        cmds.append(txt(p, "t_progress", f"{s.print.progress:.0f}%"))
        cmds.append(val(p, "j_progress", int(s.print.progress)))
    eta = _eta(s)
    if full or not old or old.print.state != s.print.state or _eta(old) != eta:
        cmds.append(txt(p, "t_eta", eta))
    pause_label = "Resume" if s.print.state == PrintState.PAUSED else "Pause"
    if full or not old or old.print.state != s.print.state:
        # Button may be image-based; visible cue also goes to t_file / t_eta.
        cmds.append(txt(p, "b_pause", pause_label))
    if full or not old or old.temps != s.temps:
        cmds += [
            txt(p, "t_hotend", f"{s.temps.hotend:.0f}/{s.temps.hotend_target:.0f}"),
            txt(p, "t_bed", f"{s.temps.bed:.0f}/{s.temps.bed_target:.0f}"),
            txt(p, "t_toolhead", _fmt_sensor(s.temps.toolhead)),
            txt(p, "t_mcu", _fmt_sensor(s.temps.mcu)),
            txt(p, "t_chamber", _fmt_sensor(s.temps.chamber)),
        ]
    if full or not old or old.ui.z_offset != s.ui.z_offset:
        cmds.append(txt(p, "t_z", f"{s.ui.z_offset:+.3f} mm"))
    return cmds


def _print_file_label(s: AppState) -> str:
    name = s.print.filename or "-"
    if s.print.state == PrintState.PAUSED:
        return f"PAUSADO: {name}"
    if s.print.state == PrintState.COMPLETE:
        return f"OK: {name}"
    if s.print.state == PrintState.CANCELLED:
        return f"CANCELADO: {name}"
    if s.print.state == PrintState.ERROR:
        return f"ERRO: {name}"
    return name


def _eta(s: AppState) -> str:
    if s.print.state == PrintState.PAUSED:
        return "PAUSADO"
    if s.print.state == PrintState.COMPLETE:
        return "FIM"
    if s.print.state == PrintState.CANCELLED:
        return "CANCEL"
    if s.print.state == PrintState.ERROR:
        return "ERRO"
    if s.print.progress <= 0.5 or s.print.print_duration <= 0:
        return "--:--"
    total = s.print.print_duration / (s.print.progress / 100.0)
    rem = max(0, total - s.print.print_duration)
    m, sec = divmod(int(rem), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _rail_fan_label(s: AppState) -> str:
    return f"{s.fans.part:.0f}%" if s.fans.part >= 1 else "OFF"


def _move_step_cmds(p: str, step: float) -> list[str]:
    """Highlight the selected step pill (pic+pic2 — USART pic==pic2 by default)."""
    cmds: list[str] = []
    for value, obj in MOVE_STEP_OBJS.items():
        inactive, active = MOVE_STEP_PICS[value]
        image = active if abs(step - value) < 1e-6 else inactive
        cmds.append(pic(p, obj, image))
        cmds.append(f"{p}.{obj}.pic2={image}")
        cmds.append(val(p, obj, 1 if abs(step - value) < 1e-6 else 0))
    return cmds


def _move(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    cmds: list[str] = []
    pos = f"X{s.move.x:.1f} Y{s.move.y:.1f} Z{s.move.z:.2f}"
    if full or not old or f"X{old.move.x:.1f} Y{old.move.y:.1f} Z{old.move.z:.2f}" != pos:
        cmds.append(txt(p, "t_pos", pos))
    hot = f"{s.temps.hotend:.0f}°C"
    bed = f"{s.temps.bed:.0f}°C"
    fan = _rail_fan_label(s)
    if full or not old or f"{old.temps.hotend:.0f}" != f"{s.temps.hotend:.0f}":
        cmds.append(txt(p, "t_rail_hotend", hot))
    if full or not old or f"{old.temps.bed:.0f}" != f"{s.temps.bed:.0f}":
        cmds.append(txt(p, "t_rail_bed", bed))
    if full or not old or _rail_fan_label(old) != fan:
        cmds.append(txt(p, "t_rail_fan", fan))
    if full or not old or abs(old.move.step - s.move.step) > 1e-9:
        cmds.extend(_move_step_cmds(p, s.move.step))
    return cmds


def _files(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    cmds: list[str] = []
    for i in range(s.files.page_size):
        idx = s.files.offset + i
        name = s.files.entries[idx] if 0 <= idx < len(s.files.entries) else ""
        mark = ">" if idx == s.files.selected and name else " "
        short = (name[-28:] if len(name) > 28 else name) if name else "-"
        cmds.append(txt(p, f"t_f{i}", f"{mark}{short}"))
    return cmds


def _fans(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    if not full and old and old.fans == s.fans:
        return []
    return [
        txt(p, "t_part", f"{s.fans.part:.0f}%"),
        txt(p, "t_side", f"{s.fans.side:.0f}%"),
        txt(p, "t_filter", f"{s.fans.filter:.0f}%"),
        val(p, "h_part", int(s.fans.part)),
        val(p, "h_side", int(s.fans.side)),
        val(p, "h_filter", int(s.fans.filter)),
    ]


def _load(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    cmds: list[str] = []
    if full or not old or old.load != s.load:
        mode_txt = (
            "Load"
            if s.load.mode == "load"
            else ("Unload" if s.load.mode == "unload" else "Load/Unload")
        )
        step2_txt = "Unload..." if s.load.mode == "unload" else "Load..."
        step3_txt = "Return completed" if s.load.mode == "unload" else "Completed"
        cmds += [
            txt(p, "t_mode", mode_txt),
            txt(p, "t_step1", "Heating"),
            txt(p, "t_step2", step2_txt),
            txt(p, "t_step3", step3_txt),
            txt(p, "t_set_temp", f"{s.load.target}°C"),
        ]
        for idx, obj in ((1, "t_step1"), (2, "t_step2"), (3, "t_step3")):
            if s.load.step == idx:
                col = 64512  # amber active
            elif s.load.step > idx:
                col = 63254  # cream done
            else:
                col = 33808  # muted
            cmds.append(f"{p}.{obj}.pco={col}")
    # Skip Nextion `vis` — USART ACK 0x1a. Idle/active layout is page-local when rebuilt.
    if full or not old or old.temps.hotend != s.temps.hotend or old.temps.hotend_target != s.temps.hotend_target or old.load != s.load:
        tgt = s.temps.hotend_target if s.temps.hotend_target > 0 else float(s.load.target)
        cmds += [
            txt(p, "t_hotend", f"{s.temps.hotend:.0f}°C"),
            txt(p, "t_hotend_tgt", f"{tgt:.0f}°C"),
        ]
    return cmds


def _zoffset(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    return [txt(p, "t_z", f"{s.ui.z_offset:+.3f} mm")]


def _calibrate(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    return [txt(p, "t_info", s.ui.status_text)]


def _network(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    # HMI atual só tem t_ip (não enviar t_host/t_ssid — ACK 0x1a).
    if full or not old or old.network.ip != s.network.ip:
        return [txt(p, "t_ip", s.network.ip or "0.0.0.0")]
    return []


def _settings(p: str, s: AppState, full: bool, old: AppState | None) -> list[str]:
    # Página settings ainda só tem a nav no .HMI.
    return []
