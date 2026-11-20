from sk1_hmi.app.state import AppState, Screen
from sk1_hmi.ui.render import render_diff, render_full


def test_render_home_contains_temps():
    s = AppState()
    s.temps.hotend = 210
    s.temps.hotend_target = 220
    s.temps.bed = 60
    s.temps.bed_target = 0
    s.temps.toolhead = 34
    s.temps.mcu = 38
    s.temps.chamber = 29
    cmds = render_full(s)
    assert any("t_hotend" in c for c in cmds)
    assert 'home.t_hotend_tgt.txt="220°C"' in cmds
    assert 'home.t_hotend_dir.txt="▲"' in cmds
    assert 'home.t_bed_tgt.txt=""' in cmds
    assert 'home.t_bed_dir.txt=""' in cmds
    assert 'home.t_toolhead.txt="34°C"' in cmds
    assert 'home.t_mcu.txt="38°C"' in cmds
    assert 'home.t_chamber.txt="29°C"' in cmds
    assert "home.b_light.pic=" in "".join(cmds)
    assert "home.b_fan.pic=" in "".join(cmds)
    assert "page 0" in cmds
    assert not any(c.startswith("vis ") for c in cmds)


def test_render_move_rails():
    s = AppState()
    s.ui.screen = Screen.MOVE
    s.temps.hotend = 28
    s.temps.bed = 31
    s.fans.part = 0
    s.move.x, s.move.y, s.move.z = 10.0, 20.0, 0.2
    cmds = render_full(s)
    assert 'move.t_pos.txt="X10.0 Y20.0 Z0.20"' in cmds
    assert 'move.t_rail_hotend.txt="28°C"' in cmds
    assert 'move.t_rail_bed.txt="31°C"' in cmds
    assert 'move.t_rail_fan.txt="OFF"' in cmds
    assert "move.b_step_1.pic=38" in cmds  # default step 1.0 → active
    assert "move.b_step_01.pic=34" in cmds  # inactive
    old = s.clone()
    s.fans.part = 100
    cmds_on = render_diff(old, s)
    assert 'move.t_rail_fan.txt="100%"' in cmds_on
    old2 = s.clone()
    s.move.step = 0.1
    cmds_step = render_diff(old2, s)
    assert "move.b_step_01.pic=35" in cmds_step
    assert "move.b_step_1.pic=37" in cmds_step


def test_render_print_contains_extra_temps_and_zoffset():
    s = AppState()
    s.ui.screen = Screen.PRINT
    s.ui.z_offset = -0.05
    s.temps.toolhead = 35
    s.temps.mcu = 40
    s.temps.chamber = 30
    cmds = render_full(s)
    assert 'print.t_toolhead.txt="35°C"' in cmds
    assert 'print.t_mcu.txt="40°C"' in cmds
    assert 'print.t_chamber.txt="30°C"' in cmds
    assert 'print.t_z.txt="-0.050 mm"' in cmds


def test_render_fans_contains_three_sliders():
    s = AppState()
    s.ui.screen = Screen.FANS
    s.fans.part = 80
    s.fans.side = 50
    s.fans.filter = 25
    cmds = render_full(s)
    assert 'fans.t_part.txt="80%"' in cmds
    assert 'fans.t_side.txt="50%"' in cmds
    assert 'fans.t_filter.txt="25%"' in cmds
    assert "fans.h_part.val=80" in cmds
    assert "fans.h_side.val=50" in cmds
    assert "fans.h_filter.val=25" in cmds


def test_render_load_idle_and_active():
    s = AppState()
    s.ui.screen = Screen.LOAD
    s.temps.hotend = 180
    s.temps.hotend_target = 0
    cmds = render_full(s)
    assert "page 5" in cmds
    assert 'loadunload.t_set_temp.txt="240°C"' in cmds

    s.load.mode = "unload"
    s.load.step = 2
    s.temps.hotend = 240
    s.temps.hotend_target = 240
    cmds_act = render_full(s)
    assert 'loadunload.t_mode.txt="Unload"' in cmds_act
    assert 'loadunload.t_step2.txt="Unload..."' in cmds_act
    assert 'loadunload.t_step3.txt="Return completed"' in cmds_act
    assert 'loadunload.t_hotend.txt="240°C"' in cmds_act
    assert not any(c.startswith("vis ") for c in cmds_act)


def test_render_diff_page_change():
    old = AppState()
    new = old.clone()
    new.ui.screen = Screen.PRINT
    cmds = render_diff(old, new)
    assert any(c.startswith("page 1") for c in cmds)


def test_render_network_ip():
    s = AppState()
    s.ui.screen = Screen.NETWORK
    s.network.ip = "192.168.0.17"
    cmds = render_full(s)
    assert "page 8" in cmds
    assert 'network.t_ip.txt="192.168.0.17"' in cmds
