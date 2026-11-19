from __future__ import annotations

from ..app.state import AppState, PrintState, Screen
from .effect import Effect, EffectKind, gcode
from .intent import IntentKind, UiIntent


NAV = {
    IntentKind.NAV_HOME: Screen.HOME,
    IntentKind.NAV_PRINT: Screen.PRINT,
    IntentKind.NAV_MOVE: Screen.MOVE,
    IntentKind.NAV_FILES: Screen.FILES,
    IntentKind.NAV_FANS: Screen.FANS,
    IntentKind.NAV_LOAD: Screen.LOAD,
    IntentKind.NAV_ZOFFSET: Screen.ZOFFSET,
    IntentKind.NAV_CALIBRATE: Screen.CALIBRATE,
    IntentKind.NAV_NETWORK: Screen.NETWORK,
    IntentKind.NAV_SETTINGS: Screen.SETTINGS,
}


def intent_blocked(state: AppState, intent: UiIntent) -> bool:
    printing = state.print.state in (PrintState.PRINTING, PrintState.PAUSED)
    if intent.kind in (
        IntentKind.MOVE_AXIS,
        IntentKind.HOME_ALL,
        IntentKind.HOME_XY,
        IntentKind.HOME_Z,
        IntentKind.EXTRUDE,
        IntentKind.LOAD_FILAMENT,
        IntentKind.UNLOAD_FILAMENT,
        IntentKind.BED_MESH,
        IntentKind.SCREW_TILT,
        IntentKind.QUAD_GANTRY,
    ) and printing:
        return True
    if intent.kind == IntentKind.START_SELECTED_FILE and state.print.state == PrintState.PRINTING:
        return True
    return False


def apply_intent(state: AppState, intent: UiIntent) -> tuple[AppState, list[Effect]]:
    """Apply local UI changes and produce effects. No optimistic printer state."""
    effects: list[Effect] = []
    s = state.clone()

    if intent.kind == IntentKind.DISPLAY_INIT:
        effects.append(Effect(kind=EffectKind.PAGE, page=s.ui.screen.value))
        return s, effects

    if intent_blocked(state, intent):
        s.ui.status_text = "Bloqueado durante impressao"
        return s, effects

    if intent.kind in NAV:
        if intent.kind == IntentKind.NAV_LOAD and s.load.step == 3:
            s.load.step = 0
            s.load.mode = ""
        s.ui.screen = NAV[intent.kind]
        effects.append(Effect(kind=EffectKind.PAGE, page=s.ui.screen.value))
        return s, effects

    if intent.kind == IntentKind.LOAD_TEMP_STEP:
        s.load.target = max(170, min(300, int(s.load.target + intent.amount)))
        return s, effects

    if intent.kind == IntentKind.SET_MOVE_STEP:
        s.move.step = intent.value
        return s, effects

    if intent.kind == IntentKind.SELECT_FILE:
        idx = s.files.offset + intent.index
        if 0 <= idx < len(s.files.entries):
            s.files.selected = idx
        return s, effects

    if intent.kind == IntentKind.FILES_PAGE_UP:
        s.files.offset = max(0, s.files.offset - s.files.page_size)
        return s, effects

    if intent.kind == IntentKind.FILES_PAGE_DOWN:
        nxt = s.files.offset + s.files.page_size
        if nxt < len(s.files.entries):
            s.files.offset = nxt
        return s, effects

    if intent.kind == IntentKind.SET_BRIGHTNESS:
        s.ui.brightness = max(0, min(100, int(intent.value)))
        effects.append(Effect(kind=EffectKind.SET_BRIGHTNESS, value=s.ui.brightness))
        return s, effects

    if intent.kind == IntentKind.RESTART_BRIDGE:
        effects.append(Effect(kind=EffectKind.RESTART_PROCESS))
        return s, effects

    # Moonraker / gcode effects
    if intent.kind == IntentKind.TOGGLE_CASE_LIGHT:
        s.lights.case_light = not state.lights.case_light
        effects.append(
            gcode(f"SET_PIN PIN=caselight VALUE={1 if s.lights.case_light else 0}")
        )
    elif intent.kind == IntentKind.PAUSE_OR_RESUME:
        if state.print.state == PrintState.PRINTING:
            effects.append(gcode("PAUSE"))
        elif state.print.state == PrintState.PAUSED:
            effects.append(gcode("RESUME"))
    elif intent.kind == IntentKind.CANCEL_PRINT:
        effects.append(gcode("CANCEL_PRINT"))
    elif intent.kind == IntentKind.HOME_ALL:
        effects.append(gcode("G28"))
    elif intent.kind == IntentKind.HOME_XY:
        effects.append(gcode("G28 X Y"))
    elif intent.kind == IntentKind.HOME_Z:
        effects.append(gcode("G28 Z"))
    elif intent.kind == IntentKind.MOVE_AXIS:
        dist = intent.amount * state.move.step
        effects.append(gcode(f"G91\nG1 {intent.axis}{dist:.3f} F3000\nG90"))
    elif intent.kind == IntentKind.EXTRUDE:
        effects.append(gcode(f"G91\nG1 E{intent.amount:.2f} F300\nG90"))
    elif intent.kind in (IntentKind.LOAD_FILAMENT, IntentKind.UNLOAD_FILAMENT):
        if state.load.step in (1, 2):
            return s, effects
        is_load = intent.kind == IntentKind.LOAD_FILAMENT
        target = s.load.target
        s.load.mode = "load" if is_load else "unload"
        s.load.step = 2 if state.temps.hotend >= target - 2 else 1
        if is_load:
            effects.append(gcode(f"M109 S{target}\nM83\nG1 E60 F300\nM82"))
        else:
            effects.append(gcode(f"M109 S{target}\nM83\nG1 E10 F300\nG1 E-70 F600\nM82"))
    elif intent.kind == IntentKind.START_SELECTED_FILE:
        if 0 <= state.files.selected < len(state.files.entries):
            name = state.files.entries[state.files.selected]
            effects.append(gcode(f"SDCARD_PRINT_FILE FILENAME=\"{name}\""))
    elif intent.kind == IntentKind.SET_PART_FAN:
        effects.append(gcode(f"M106 S{int(max(0, min(255, intent.value * 2.55)))}"))
    elif intent.kind == IntentKind.TOGGLE_PART_FAN:
        # b_fan na home: liga em 100% se estiver parado, desliga se já girando
        new_val = 0 if state.fans.part >= 50 else 100
        s.fans.part = float(new_val)
        effects.append(gcode(f"M106 S{int(new_val * 2.55)}"))
    elif intent.kind == IntentKind.SET_SIDE_FAN:
        effects.append(gcode(f"SET_FAN_SPEED FAN=Side_fan SPEED={intent.value/100:.2f}"))
    elif intent.kind == IntentKind.SET_FILTER_FAN:
        effects.append(gcode(f"SET_FAN_SPEED FAN=Filter_fan SPEED={intent.value/100:.2f}"))
    elif intent.kind == IntentKind.BABY_STEP:
        s.ui.z_offset = round(s.ui.z_offset + intent.amount, 3)
        effects.append(gcode(f"SET_GCODE_OFFSET Z_ADJUST={intent.amount:.3f} MOVE=1"))
    elif intent.kind == IntentKind.SAVE_CONFIG:
        effects.append(gcode("SAVE_CONFIG"))
    elif intent.kind == IntentKind.BED_MESH:
        effects.append(gcode("BED_MESH_CALIBRATE"))
    elif intent.kind == IntentKind.SCREW_TILT:
        effects.append(gcode("SCREW_TILT_CALCULATE"))
    elif intent.kind == IntentKind.QUAD_GANTRY:
        effects.append(gcode("QUAD_GANTRY_LEVEL"))

    return s, effects
