from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum, auto


class Screen(Enum):
    HOME = 0
    PRINT = 1
    MOVE = 2
    FILES = 3
    FANS = 4
    LOAD = 5
    ZOFFSET = 6
    CALIBRATE = 7
    NETWORK = 8
    SETTINGS = 9


class PrintState(Enum):
    STANDBY = auto()
    PRINTING = auto()
    PAUSED = auto()
    COMPLETE = auto()
    ERROR = auto()
    CANCELLED = auto()


@dataclass
class TemperatureState:
    hotend: float = 0.0
    hotend_target: float = 0.0
    bed: float = 0.0
    bed_target: float = 0.0
    toolhead: float | None = None
    mcu: float | None = None
    chamber: float | None = None


@dataclass
class FanState:
    part: float = 0.0
    side: float = 0.0
    filter: float = 0.0


@dataclass
class LightState:
    case_light: bool = False


@dataclass
class PrintInfo:
    state: PrintState = PrintState.STANDBY
    filename: str = ""
    progress: float = 0.0
    print_duration: float = 0.0
    message: str = ""


@dataclass
class MoveState:
    step: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    homed: str = ""


@dataclass
class FilesState:
    entries: list[str] = field(default_factory=list)
    offset: int = 0
    selected: int = -1
    page_size: int = 5


@dataclass
class NetworkState:
    hostname: str = ""
    ip: str = ""
    ssid: str = ""


@dataclass
class LoadState:
    mode: str = ""  # "" | "load" | "unload"
    step: int = 0   # 0 = idle, 1 = heating, 2 = feeding/retracting, 3 = completed
    target: int = 240


@dataclass
class UiState:
    screen: Screen = Screen.HOME
    brightness: int = 80
    z_offset: float = 0.0
    status_text: str = "Ready"
    about: str = "sk1-hmi 0.1.0"


@dataclass
class AppState:
    ui: UiState = field(default_factory=UiState)
    temps: TemperatureState = field(default_factory=TemperatureState)
    fans: FanState = field(default_factory=FanState)
    lights: LightState = field(default_factory=LightState)
    print: PrintInfo = field(default_factory=PrintInfo)
    move: MoveState = field(default_factory=MoveState)
    load: LoadState = field(default_factory=LoadState)
    files: FilesState = field(default_factory=FilesState)
    network: NetworkState = field(default_factory=NetworkState)
    connected: bool = False

    def clone(self) -> "AppState":
        return replace(
            self,
            ui=replace(self.ui),
            temps=replace(self.temps),
            fans=replace(self.fans),
            lights=replace(self.lights),
            print=replace(self.print),
            move=replace(self.move),
            load=replace(self.load),
            files=replace(self.files, entries=list(self.files.entries)),
            network=replace(self.network),
        )
