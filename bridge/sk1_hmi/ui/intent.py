from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class IntentKind(Enum):
    NAV_HOME = auto()
    NAV_PRINT = auto()
    NAV_MOVE = auto()
    NAV_FILES = auto()
    NAV_FANS = auto()
    NAV_LOAD = auto()
    NAV_ZOFFSET = auto()
    NAV_CALIBRATE = auto()
    NAV_NETWORK = auto()
    NAV_SETTINGS = auto()
    TOGGLE_CASE_LIGHT = auto()
    PAUSE_OR_RESUME = auto()
    CANCEL_PRINT = auto()
    HOME_ALL = auto()
    HOME_XY = auto()
    HOME_Z = auto()
    MOVE_AXIS = auto()
    SET_MOVE_STEP = auto()
    EXTRUDE = auto()
    LOAD_TEMP_STEP = auto()
    LOAD_FILAMENT = auto()
    UNLOAD_FILAMENT = auto()
    SELECT_FILE = auto()
    FILES_PAGE_UP = auto()
    FILES_PAGE_DOWN = auto()
    START_SELECTED_FILE = auto()
    SET_PART_FAN = auto()
    TOGGLE_PART_FAN = auto()
    SET_SIDE_FAN = auto()
    SET_FILTER_FAN = auto()
    BABY_STEP = auto()
    SAVE_CONFIG = auto()
    BED_MESH = auto()
    SCREW_TILT = auto()
    QUAD_GANTRY = auto()
    SET_BRIGHTNESS = auto()
    RESTART_BRIDGE = auto()
    DISPLAY_INIT = auto()


@dataclass(frozen=True)
class UiIntent:
    kind: IntentKind
    axis: str = ""
    amount: float = 0.0
    index: int = 0
    value: float = 0.0
