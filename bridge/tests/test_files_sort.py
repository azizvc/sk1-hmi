from sk1_hmi.moonraker.client import sort_files_newest_first


def test_sort_files_newest_first():
    items = [
        {"path": "old.gcode", "modified": 100.0},
        {"path": "new.gcode", "modified": 300.0},
        {"path": "mid.gcode", "modified": 200.0},
        {"path": "also_new.gcode", "modified": 300.0},
        {"size": 1},  # ignored
    ]
    assert sort_files_newest_first(items) == [
        "also_new.gcode",
        "new.gcode",
        "mid.gcode",
        "old.gcode",
    ]


def test_sort_files_handles_bad_modified():
    items = [
        {"path": "a.gcode", "modified": "nope"},
        {"path": "b.gcode", "modified": 50},
    ]
    assert sort_files_newest_first(items) == ["b.gcode", "a.gcode"]
