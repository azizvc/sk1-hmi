from __future__ import annotations

from .intent import IntentKind, UiIntent


# (page, component) -> intent factory
_ROUTE: dict[tuple[int, int], UiIntent] = {}


def _put(page: int, component: int, intent: UiIntent) -> None:
    _ROUTE[(page, component)] = intent


# Nav ids differ per page after USART reorders objects (see hmi/sk1-hmi.HMI.ids.json).
_NAV: dict[int, tuple[int, int, int, int, int]] = {
    # (home, print, move, files, more)
    0: (1, 2, 3, 4, 5),
    1: (15, 16, 17, 18, 19),
    2: (20, 21, 22, 23, 24),       # wifi removido → nav desceu 1
    3: (16, 17, 18, 19, 20),
    4: (10, 11, 12, 13, 14),       # wifi removido → nav desceu 1
    5: (4, 8, 5, 6, 7),            # loadunload: tabs 1..3, depois nav
    6: (1, 2, 3, 4, 5),
    7: (1, 2, 3, 4, 5),
    8: (1, 2, 3, 4, 5),
    9: (1, 2, 3, 4, 5),
}


def _nav_bar(page: int) -> None:
    home, prt, move, files, more = _NAV.get(page, _NAV[0])
    _put(page, home, UiIntent(IntentKind.NAV_HOME))
    _put(page, prt, UiIntent(IntentKind.NAV_PRINT))
    _put(page, move, UiIntent(IntentKind.NAV_MOVE))
    _put(page, files, UiIntent(IntentKind.NAV_FILES))
    _put(page, more, UiIntent(IntentKind.NAV_SETTINGS))


for p in range(10):
    _nav_bar(p)

# ---------------------------------------------------------------------------
# 0: home — p_wifi only here + print
# ---------------------------------------------------------------------------
_put(0, 6, UiIntent(IntentKind.TOGGLE_CASE_LIGHT))            # b_light
_put(0, 7, UiIntent(IntentKind.TOGGLE_PART_FAN))              # b_fan
_put(0, 8, UiIntent(IntentKind.NAV_NETWORK))                  # p_wifi → IP
_put(0, 19, UiIntent(IntentKind.NAV_MOVE))                    # t_hotend_lbl
_put(0, 20, UiIntent(IntentKind.NAV_MOVE))                    # t_bed_lbl

# ---------------------------------------------------------------------------
# 1: print
# ---------------------------------------------------------------------------
_put(1, 2, UiIntent(IntentKind.NAV_NETWORK))                  # p_wifi → IP
_put(1, 4, UiIntent(IntentKind.PAUSE_OR_RESUME))              # b_pause
_put(1, 5, UiIntent(IntentKind.CANCEL_PRINT))                 # b_cancel
_put(1, 21, UiIntent(IntentKind.BABY_STEP, amount=-0.025))    # b_z_m
_put(1, 22, UiIntent(IntentKind.BABY_STEP, amount=0.025))     # b_z_p

# ---------------------------------------------------------------------------
# 2: move (sem p_wifi)
# ---------------------------------------------------------------------------
_put(2, 3, UiIntent(IntentKind.MOVE_AXIS, axis="Y", amount=1))     # b_y_p
_put(2, 4, UiIntent(IntentKind.MOVE_AXIS, axis="Z", amount=1))     # b_z_p
_put(2, 5, UiIntent(IntentKind.MOVE_AXIS, axis="X", amount=-1))    # b_x_m
_put(2, 6, UiIntent(IntentKind.NAV_MOVE))                          # b_tab_move
_put(2, 7, UiIntent(IntentKind.MOVE_AXIS, axis="X", amount=1))     # b_x_p
_put(2, 8, UiIntent(IntentKind.MOVE_AXIS, axis="Y", amount=-1))    # b_y_m
_put(2, 9, UiIntent(IntentKind.MOVE_AXIS, axis="Z", amount=-1))    # b_z_m
_put(2, 10, UiIntent(IntentKind.HOME_XY))                          # b_home_xy
_put(2, 11, UiIntent(IntentKind.HOME_Z))                           # b_home_z
_put(2, 12, UiIntent(IntentKind.SET_MOVE_STEP, value=0.1))         # b_step_01
_put(2, 13, UiIntent(IntentKind.SET_MOVE_STEP, value=1.0))         # b_step_1
_put(2, 14, UiIntent(IntentKind.SET_MOVE_STEP, value=10.0))        # b_step_10
_put(2, 15, UiIntent(IntentKind.SET_MOVE_STEP, value=30.0))        # b_step_30
_put(2, 16, UiIntent(IntentKind.NAV_LOAD))                         # b_tab_load
_put(2, 17, UiIntent(IntentKind.NAV_FANS))                         # b_tab_fan

# ---------------------------------------------------------------------------
# 3: files
# ---------------------------------------------------------------------------
for i in range(5):
    _put(3, 8 + i, UiIntent(IntentKind.SELECT_FILE, index=i))
_put(3, 13, UiIntent(IntentKind.FILES_PAGE_UP))               # b_up
_put(3, 14, UiIntent(IntentKind.FILES_PAGE_DOWN))             # b_down
_put(3, 15, UiIntent(IntentKind.START_SELECTED_FILE))         # b_print

# ---------------------------------------------------------------------------
# 4: fans (sem p_wifi; sliders 7/8/9)
# ---------------------------------------------------------------------------
_put(4, 1, UiIntent(IntentKind.NAV_MOVE))                     # b_tab_move
_put(4, 2, UiIntent(IntentKind.NAV_LOAD))                     # b_tab_load
_put(4, 3, UiIntent(IntentKind.NAV_FANS))                     # b_tab_fan

# ---------------------------------------------------------------------------
# 5: loadunload
# ---------------------------------------------------------------------------
_put(5, 1, UiIntent(IntentKind.NAV_MOVE))                     # b_tab_move
_put(5, 2, UiIntent(IntentKind.NAV_LOAD))                     # b_tab_load
_put(5, 3, UiIntent(IntentKind.NAV_FANS))                     # b_tab_fan
_put(5, 14, UiIntent(IntentKind.LOAD_TEMP_STEP, amount=-10))  # b_temp_m
_put(5, 15, UiIntent(IntentKind.LOAD_TEMP_STEP, amount=10))   # b_temp_p
_put(5, 16, UiIntent(IntentKind.LOAD_FILAMENT))               # b_load
_put(5, 17, UiIntent(IntentKind.UNLOAD_FILAMENT))             # b_unload


def route_touch(page: int, component: int) -> UiIntent | None:
    return _ROUTE.get((page, component))


def route_slider(page: int, component: int, value: int) -> UiIntent | None:
    # Sliders da page 4 (fans): h_part=7, h_side=8, h_filter=9
    if page == 4 and component in (7, 8, 9):
        kind = {
            7: IntentKind.SET_PART_FAN,
            8: IntentKind.SET_SIDE_FAN,
            9: IntentKind.SET_FILTER_FAN,
        }[component]
        return UiIntent(kind, value=float(value))
    if page == 9 and component == 11:
        return UiIntent(IntentKind.SET_BRIGHTNESS, value=float(value))
    return None
