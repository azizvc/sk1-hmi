from __future__ import annotations

from ..app.state import Screen


def page_name(screen: Screen) -> str:
    return {
        Screen.HOME: "home",
        Screen.PRINT: "print",
        Screen.MOVE: "move",
        Screen.FILES: "files",
        Screen.FANS: "fans",
        Screen.LOAD: "loadunload",
        Screen.ZOFFSET: "zoffset",
        Screen.CALIBRATE: "calibrate",
        Screen.NETWORK: "network",
        Screen.SETTINGS: "settings",
    }[screen]


def txt(page: str, obj: str, value: str) -> str:
    safe = value.replace('"', "'")
    return f'{page}.{obj}.txt="{safe}"'


def val(page: str, obj: str, value: int) -> str:
    return f"{page}.{obj}.val={int(value)}"


def pic(page: str, obj: str, image_id: int) -> str:
    return f"{page}.{obj}.pic={int(image_id)}"


def page(n: int) -> str:
    return f"page {n}"


def dim(percent: int) -> str:
    return f"dim={max(0, min(100, percent))}"


# USART image library indices (pairs: OFF = default on the .HMI component)
PIC_FAN_OFF = 13
PIC_FAN_ON = 14
PIC_LIGHT_OFF = 15
PIC_LIGHT_ON = 16

# Move step pills: (inactive, active). Defaults on the component are the inactive ids.
MOVE_STEP_PICS: dict[float, tuple[int, int]] = {
    0.1: (34, 35),
    1.0: (37, 38),
    10.0: (39, 40),
    30.0: (41, 42),
}
MOVE_STEP_OBJS: dict[float, str] = {
    0.1: "b_step_01",
    1.0: "b_step_1",
    10.0: "b_step_10",
    30.0: "b_step_30",
}
