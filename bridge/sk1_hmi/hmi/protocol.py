from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


TERM = b"\xff\xff\xff"


class HmiEventKind(Enum):
    TOUCH = auto()
    NUMERIC = auto()
    INIT = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class HmiEvent:
    kind: HmiEventKind
    page: int = 0
    component: int = 0
    value: int = 0
    raw: bytes = b""


def encode_command(cmd: str) -> bytes:
    return cmd.encode("iso-8859-1", errors="ignore") + TERM


def parse_frame(frame: bytes) -> HmiEvent | None:
    if not frame:
        return None
    # TJC/Nextion: 0x65 page component event — touch
    if frame[0] == 0x65 and len(frame) >= 4:
        return HmiEvent(
            kind=HmiEventKind.TOUCH,
            page=frame[1],
            component=frame[2],
            value=frame[3],
            raw=frame,
        )
    # numeric / slider often 0x71 + 4-byte LE int after write request; also 0x72 custom
    if frame[0] == 0x71 and len(frame) >= 5:
        val = int.from_bytes(frame[1:5], "little", signed=False)
        return HmiEvent(kind=HmiEventKind.NUMERIC, value=val, raw=frame)
    # SK1 stock init byte seen in community reverse engineering
    if frame == b"\x91" or (len(frame) == 1 and frame[0] == 0x91):
        return HmiEvent(kind=HmiEventKind.INIT, raw=frame)
    return HmiEvent(kind=HmiEventKind.UNKNOWN, raw=frame)


class FrameBuffer:
    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, data: bytes) -> list[HmiEvent]:
        events: list[HmiEvent] = []
        self._buf.extend(data)
        # Lone init byte without terminator
        while self._buf and self._buf[0] == 0x91:
            events.append(HmiEvent(kind=HmiEventKind.INIT, raw=b"\x91"))
            del self._buf[0]
        while True:
            idx = self._buf.find(TERM)
            if idx < 0:
                # keep buffer bounded
                if len(self._buf) > 512:
                    del self._buf[:-64]
                break
            frame = bytes(self._buf[:idx])
            del self._buf[: idx + 3]
            ev = parse_frame(frame)
            if ev:
                events.append(ev)
        return events
