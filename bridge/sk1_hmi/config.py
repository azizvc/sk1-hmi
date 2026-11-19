from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class HmiConfig:
    serial: str = "/dev/ttyS1"
    baud: int = 115200
    dry_run: bool = False


@dataclass
class MoonrakerConfig:
    host: str = "127.0.0.1"
    port: int = 7125
    api_key: str = ""


@dataclass
class LogConfig:
    level: str = "info"


@dataclass
class AppConfig:
    hmi: HmiConfig = field(default_factory=HmiConfig)
    moonraker: MoonrakerConfig = field(default_factory=MoonrakerConfig)
    log: LogConfig = field(default_factory=LogConfig)


def load_config(path: str | Path) -> AppConfig:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    h = data.get("hmi", {})
    m = data.get("moonraker", {})
    l = data.get("log", {})
    return AppConfig(
        hmi=HmiConfig(
            serial=h.get("serial", "/dev/ttyS1"),
            baud=int(h.get("baud", 115200)),
            dry_run=bool(h.get("dry_run", False)),
        ),
        moonraker=MoonrakerConfig(
            host=m.get("host", "127.0.0.1"),
            port=int(m.get("port", 7125)),
            api_key=m.get("api_key", ""),
        ),
        log=LogConfig(level=l.get("level", "info")),
    )
