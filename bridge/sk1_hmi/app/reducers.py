from __future__ import annotations

from typing import Any

from .state import AppState, PrintState


_PRINT_MAP = {
    "standby": PrintState.STANDBY,
    "printing": PrintState.PRINTING,
    "paused": PrintState.PAUSED,
    "complete": PrintState.COMPLETE,
    "error": PrintState.ERROR,
    "cancelled": PrintState.CANCELLED,
}


def extract_status(message: dict[str, Any]) -> dict[str, Any] | None:
    """Pull printer status from Moonraker HTTP result or WS notify payloads."""
    params = message.get("params")
    # notify_status_update: params = [status_dict, eventtime]
    if isinstance(params, list) and params:
        first = params[0]
        if isinstance(first, dict):
            nested = first.get("status")
            if isinstance(nested, dict):
                return nested
            return first
    if isinstance(params, dict):
        nested = params.get("status")
        if isinstance(nested, dict):
            return nested
    result = message.get("result")
    if isinstance(result, dict):
        nested = result.get("status")
        if isinstance(nested, dict):
            return nested
    return None


def reduce_moonraker(state: AppState, message: dict[str, Any]) -> AppState:
    s = state.clone()
    s.connected = True
    status = extract_status(message)
    if not isinstance(status, dict):
        return s

    if "extruder" in status:
        e = status["extruder"] or {}
        if "temperature" in e:
            s.temps.hotend = float(e["temperature"])
        if "target" in e:
            s.temps.hotend_target = float(e["target"])
    if "heater_bed" in status:
        b = status["heater_bed"] or {}
        if "temperature" in b:
            s.temps.bed = float(b["temperature"])
        if "target" in b:
            s.temps.bed_target = float(b["target"])
    for key, obj in status.items():
        if not isinstance(obj, dict) or "temperature" not in obj or obj["temperature"] is None:
            continue
        low = key.lower()
        if not (low.startswith("temperature_sensor ") or low.startswith("temperature_fan ") or low.startswith("temperature_host ")):
            continue
        val = float(obj["temperature"])
        if "toolboard" in low or "toolhead" in low or "thr" in low:
            s.temps.toolhead = val
        elif "chamber" in low or "enclosure" in low:
            s.temps.chamber = val
        elif "mcu" in low:
            s.temps.mcu = val
    if "fan" in status and "speed" in (status["fan"] or {}):
        s.fans.part = float(status["fan"]["speed"]) * 100.0
    if "fan_generic Side_fan" in status and "speed" in (
        status["fan_generic Side_fan"] or {}
    ):
        s.fans.side = float(status["fan_generic Side_fan"]["speed"]) * 100.0
    if "fan_generic Filter_fan" in status and "speed" in (
        status["fan_generic Filter_fan"] or {}
    ):
        s.fans.filter = float(status["fan_generic Filter_fan"]["speed"]) * 100.0
    if "output_pin caselight" in status and "value" in (
        status["output_pin caselight"] or {}
    ):
        s.lights.case_light = float(status["output_pin caselight"]["value"]) > 0.5
    if "toolhead" in status:
        th = status["toolhead"] or {}
        pos = th.get("position")
        if isinstance(pos, list) and len(pos) >= 3:
            s.move.x, s.move.y, s.move.z = float(pos[0]), float(pos[1]), float(pos[2])
        if "homed_axes" in th:
            s.move.homed = str(th["homed_axes"])
    if "gcode_move" in status:
        gm = status["gcode_move"] or {}
        ho = gm.get("homing_origin")
        if isinstance(ho, list) and len(ho) >= 3 and ho[2] is not None:
            s.ui.z_offset = float(ho[2])
    if "print_stats" in status:
        ps = status["print_stats"] or {}
        # Moonraker WS sends partial objects — only apply keys that are present
        if "state" in ps:
            st = str(ps.get("state") or "standby").lower()
            s.print.state = _PRINT_MAP.get(st, PrintState.STANDBY)
            s.ui.status_text = s.print.state.name.title()
        if "filename" in ps:
            s.print.filename = str(ps["filename"] or "")
        if "print_duration" in ps:
            s.print.print_duration = float(ps["print_duration"] or 0)
        if "message" in ps:
            s.print.message = str(ps["message"] or "")
    if "virtual_sdcard" in status and "progress" in (status["virtual_sdcard"] or {}):
        s.print.progress = float(status["virtual_sdcard"]["progress"] or 0) * 100.0
    # During initial heat soak, show Heating instead of bare Printing
    if (
        s.print.state == PrintState.PRINTING
        and s.print.print_duration <= 0
        and (
            (s.temps.hotend_target > 0 and s.temps.hotend + 2 < s.temps.hotend_target)
            or (s.temps.bed_target > 0 and s.temps.bed + 2 < s.temps.bed_target)
        )
    ):
        s.ui.status_text = "Heating"
    if "display_status" in status:
        msg = (status["display_status"] or {}).get("message")
        if msg:
            s.ui.status_text = str(msg)
    if (
        s.load.mode in ("load", "unload")
        and s.load.step == 1
        and s.temps.hotend >= s.load.target - 2
    ):
        s.load.step = 2
    return s
