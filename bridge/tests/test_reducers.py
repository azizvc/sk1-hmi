from sk1_hmi.app.reducers import extract_status, reduce_moonraker
from sk1_hmi.app.state import AppState, PrintState


def test_extract_notify_status_update_list():
    msg = {
        "method": "notify_status_update",
        "params": [{"print_stats": {"state": "printing", "filename": "a.gcode"}}, 12.3],
    }
    status = extract_status(msg)
    assert status is not None
    assert status["print_stats"]["state"] == "printing"


def test_extract_http_result():
    msg = {"result": {"status": {"extruder": {"temperature": 21.0}}}}
    assert extract_status(msg)["extruder"]["temperature"] == 21.0


def test_reduce_notify_sets_printing():
    state = AppState()
    msg = {
        "method": "notify_status_update",
        "params": [
            {
                "print_stats": {
                    "state": "printing",
                    "filename": "part.gcode",
                    "print_duration": 0,
                    "message": "",
                },
                "virtual_sdcard": {"progress": 0.12},
            },
            99.0,
        ],
    }
    new = reduce_moonraker(state, msg)
    assert new.print.state == PrintState.PRINTING
    assert new.print.filename == "part.gcode"
    assert abs(new.print.progress - 12.0) < 0.01
    assert new.ui.status_text == "Printing"


def test_partial_print_stats_keeps_state():
    state = AppState()
    state.print.state = PrintState.PRINTING
    state.print.filename = "part.gcode"
    state.ui.status_text = "Printing"
    msg = {
        "method": "notify_status_update",
        "params": [{"print_stats": {"print_duration": 1.5}}, 1.0],
    }
    new = reduce_moonraker(state, msg)
    assert new.print.state == PrintState.PRINTING
    assert new.print.filename == "part.gcode"
    assert new.print.print_duration == 1.5


def test_reduce_extra_temp_sensors():
    state = AppState()
    msg = {
        "result": {
            "status": {
                "temperature_sensor toolboard": {"temperature": 33.6},
                "temperature_sensor mcu": {"temperature": 41.2},
                "temperature_sensor chamber": {"temperature": 28.4},
            }
        }
    }
    new = reduce_moonraker(state, msg)
    assert abs(new.temps.toolhead - 33.6) < 0.01
    assert abs(new.temps.mcu - 41.2) < 0.01
    assert abs(new.temps.chamber - 28.4) < 0.01
