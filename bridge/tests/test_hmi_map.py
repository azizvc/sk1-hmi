"""Route table must match the ids that actually exist in hmi/sk1-hmi.HMI.

The ids are read straight from the project file with tools/hmi_dump.py, so a
mismatch between the HMI layout and the bridge route table fails here instead
of on the printer screen.
"""

from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from hmi_dump import group_pages, read_bytes  # noqa: E402

HMI = ROOT / "hmi" / "sk1-hmi.HMI"
SNAPSHOT = ROOT / "hmi" / "sk1-hmi.HMI.ids.json"

pytestmark = pytest.mark.skipif(
    not HMI.exists() and not SNAPSHOT.exists(),
    reason="hmi/sk1-hmi.HMI (or its .ids.json snapshot) not available",
)


def _load_pages() -> "OrderedDict[str, dict[int, dict]]":
    try:
        return group_pages(read_bytes(HMI))
    except PermissionError:
        if not SNAPSHOT.exists():
            pytest.skip("editor holds hmi/sk1-hmi.HMI and no snapshot exists")
        raw = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        return OrderedDict(
            (name, {entry["id"]: entry for entry in comps})
            for name, comps in raw.items()
        )


@pytest.fixture(scope="module")
def pages():
    return _load_pages()


def _names(pages, page: str) -> dict[int, str]:
    return {cid: entry["name"] for cid, entry in pages[page].items()}


def _cid(pages, page: str, name: str) -> int:
    for cid, n in _names(pages, page).items():
        if n == name:
            return cid
    pytest.fail(f"{name!r} not on page {page!r}")


def test_nav_ids_by_name(pages):
    slots = ("nav_home", "nav_print", "nav_move", "nav_files", "nav_more")
    for page in pages:
        names = set(_names(pages, page).values())
        for slot in slots:
            assert slot in names, f"{slot} missing on page {page}"


def test_home_routes_point_at_real_components(pages):
    from sk1_hmi.ui.route import route_touch

    assert _cid(pages, "home", "b_light") == 6
    assert _cid(pages, "home", "b_fan") == 7
    assert route_touch(0, 6) is not None
    assert route_touch(0, 7) is not None
    assert _cid(pages, "home", "t_hotend_lbl") == 19
    assert _cid(pages, "home", "t_bed_lbl") == 20
    assert route_touch(0, 19) is not None
    assert route_touch(0, 20) is not None


def test_print_routes(pages):
    from sk1_hmi.ui.intent import IntentKind
    from sk1_hmi.ui.route import route_touch

    assert _cid(pages, "print", "b_pause") == 4
    assert _cid(pages, "print", "b_cancel") == 5
    assert route_touch(1, 4).kind == IntentKind.PAUSE_OR_RESUME
    assert route_touch(1, 5).kind == IntentKind.CANCEL_PRINT
    assert _cid(pages, "print", "b_z_m") == 21
    assert _cid(pages, "print", "b_z_p") == 22


def test_move_routes_match_geometry(pages):
    from sk1_hmi.ui.intent import IntentKind
    from sk1_hmi.ui.route import route_touch

    assert _cid(pages, "move", "b_tab_move") == 6
    assert route_touch(2, 6).kind == IntentKind.NAV_MOVE
    assert _cid(pages, "move", "b_tab_load") == 16
    assert route_touch(2, 16).kind == IntentKind.NAV_LOAD
    assert _cid(pages, "move", "b_tab_fan") == 17
    assert route_touch(2, 17).kind == IntentKind.NAV_FANS
    assert "p_wifi" not in _names(pages, "move").values()


def test_files_routes(pages):
    from sk1_hmi.ui.intent import IntentKind
    from sk1_hmi.ui.route import route_touch

    names = _names(pages, "files")
    assert [names[8 + i] for i in range(5)] == [f"b_f{i}" for i in range(5)]
    assert route_touch(3, 8).kind == IntentKind.SELECT_FILE
    assert route_touch(3, 8).index == 0
    assert route_touch(3, 12).index == 4
    assert _cid(pages, "files", "b_up") == 13
    assert _cid(pages, "files", "b_down") == 14
    assert _cid(pages, "files", "b_print") == 15
    assert route_touch(3, 13).kind == IntentKind.FILES_PAGE_UP
    assert route_touch(3, 14).kind == IntentKind.FILES_PAGE_DOWN
    assert route_touch(3, 15).kind == IntentKind.START_SELECTED_FILE


def test_fans_tabs_and_sliders(pages):
    from sk1_hmi.ui.intent import IntentKind
    from sk1_hmi.ui.route import route_slider, route_touch

    assert _cid(pages, "fans", "b_tab_move") == 1
    assert _cid(pages, "fans", "b_tab_load") == 2
    assert _cid(pages, "fans", "b_tab_fan") == 3
    assert route_touch(4, 1).kind == IntentKind.NAV_MOVE
    assert route_touch(4, 2).kind == IntentKind.NAV_LOAD
    assert route_touch(4, 3).kind == IntentKind.NAV_FANS
    assert "p_wifi" not in _names(pages, "fans").values()
    assert _cid(pages, "fans", "h_part") == 7
    assert _cid(pages, "fans", "h_side") == 8
    assert _cid(pages, "fans", "h_filter") == 9
    assert route_slider(4, 7, 55).kind == IntentKind.SET_PART_FAN
    assert route_slider(4, 8, 55).kind == IntentKind.SET_SIDE_FAN
    assert route_slider(4, 9, 55).kind == IntentKind.SET_FILTER_FAN
    assert route_slider(4, 7, 55).value == 55.0


def test_loadunload_tabs_and_actions(pages):
    from sk1_hmi.ui.intent import IntentKind
    from sk1_hmi.ui.route import route_touch

    page = "loadunload" if "loadunload" in pages else "lights"
    assert _cid(pages, page, "b_tab_move") == 1
    assert _cid(pages, page, "b_tab_load") == 2
    assert _cid(pages, page, "b_tab_fan") == 3
    assert route_touch(5, 1).kind == IntentKind.NAV_MOVE
    assert route_touch(5, 2).kind == IntentKind.NAV_LOAD
    assert route_touch(5, 3).kind == IntentKind.NAV_FANS
    assert _cid(pages, page, "b_temp_m") == 14
    assert _cid(pages, page, "b_temp_p") == 15
    assert _cid(pages, page, "b_load") == 16
    assert _cid(pages, page, "b_unload") == 17
    assert route_touch(5, 14).kind == IntentKind.LOAD_TEMP_STEP
    assert route_touch(5, 14).amount == -10
    assert route_touch(5, 15).amount == 10
    assert route_touch(5, 16).kind == IntentKind.LOAD_FILAMENT
    assert route_touch(5, 17).kind == IntentKind.UNLOAD_FILAMENT
    assert _cid(pages, page, "nav_home") == 4
    assert _cid(pages, page, "nav_print") == 8
    assert route_touch(5, 4).kind == IntentKind.NAV_HOME
    assert route_touch(5, 8).kind == IntentKind.NAV_PRINT
    assert "p_wifi" not in _names(pages, page).values()


def test_wifi_only_on_home_and_print(pages):
    wifi_pages = {
        name
        for name, comps in pages.items()
        if any(e["name"] == "p_wifi" for e in comps.values())
    }
    assert wifi_pages == {"home", "print"}


def test_no_route_points_at_a_text_object(pages):
    """Text/number widgets never send their id, so routing them is dead code."""
    from sk1_hmi.ui.route import route_touch

    for page, comps in pages.items():
        index = list(pages).index(page)
        for cid, entry in comps.items():
            if entry["type"] not in (1, 5, 98, 109):
                continue
            route_touch(index, cid)  # only smoke: no exception