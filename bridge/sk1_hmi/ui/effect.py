from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class EffectKind(Enum):
    GCODE = auto()
    RESTART_PROCESS = auto()
    SET_BRIGHTNESS = auto()
    PAGE = auto()


@dataclass(frozen=True)
class Effect:
    kind: EffectKind
    script: str = ""
    page: int = 0
    value: int = 0


def gcode(script: str) -> Effect:
    return Effect(kind=EffectKind.GCODE, script=script)
