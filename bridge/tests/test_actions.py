from sk1_hmi.app.state import AppState, PrintState
from sk1_hmi.ui.action_handler import apply_intent, intent_blocked
from sk1_hmi.ui.intent import IntentKind, UiIntent
from sk1_hmi.ui.route import route_touch


def test_route_home_print_button():
    intent = route_touch(0, 2)
    assert intent is not None
    assert intent.kind == IntentKind.NAV_PRINT


def test_wifi_opens_network_for_ip():
    # p_wifi → network (t_ip)
    assert route_touch(0, 8).kind == IntentKind.NAV_NETWORK
    assert route_touch(1, 2).kind == IntentKind.NAV_NETWORK
    assert route_touch(2, 15).kind == IntentKind.NAV_NETWORK
    assert route_touch(4, 4).kind == IntentKind.NAV_NETWORK
    s = AppState()
    s2, effects = apply_intent(s, UiIntent(IntentKind.NAV_NETWORK))
    assert s2.ui.screen.name == "NETWORK"
    assert effects and effects[0].page == 8


def test_load_and_unload_routes_and_effects():
    s = AppState()
    s.temps.hotend = 25.0
    s.load.target = 240
    # ids reais (hmi/sk1-hmi.HMI.ids.json): page 2 move — b_tab_load=17
    assert route_touch(2, 17).kind == IntentKind.NAV_LOAD
    assert route_touch(5, 6).kind == IntentKind.NAV_MOVE
    assert route_touch(5, 8).kind == IntentKind.NAV_FANS

    s2, eff = apply_intent(s, UiIntent(IntentKind.LOAD_FILAMENT))
    assert s2.load.mode == "load"
    assert s2.load.step == 1
    assert eff and "M109 S240" in eff[0].script and "G1 E60" in eff[0].script

    s.temps.hotend = 240.0
    s3, eff2 = apply_intent(s, UiIntent(IntentKind.UNLOAD_FILAMENT))
    assert s3.load.mode == "unload"
    assert s3.load.step == 2
    assert eff2 and "G1 E-70" in eff2[0].script


def test_move_blocked_while_printing():
    state = AppState()
    state.print.state = PrintState.PRINTING
    intent = UiIntent(IntentKind.MOVE_AXIS, axis="X", amount=1)
    assert intent_blocked(state, intent) is True
    new_state, effects = apply_intent(state, intent)
    assert effects == []
    assert "Bloqueado" in new_state.ui.status_text


def test_toggle_light_effect():
    state = AppState()
    _, effects = apply_intent(state, UiIntent(IntentKind.TOGGLE_CASE_LIGHT))
    assert effects
    assert "SET_PIN PIN=caselight" in effects[0].script
