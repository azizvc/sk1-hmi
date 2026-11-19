/**
 * Mock USART HMI — componentes absolutos espelhando docs/component-map.md
 * Modelo: TJC4827X243_011C · 480×272
 * Visual: stock TwoTrees SK1 (charcoal + amber glow) com fundos e sprites recortados
 *
 * Cada comp: { id, obj, type, x, y, w, h, text?, icon?, sprite?, className?, intent? }
 */

const W = 480;
const H = 272;
const ICON_BASE = "../../assets/icons";
const UI_BASE = "../../assets/ui";
const VER = "33";

// Estado interativo do mock para testar sprites e toggles
const sim = {
  lightOn: true,
  fanOn: false,
  fans: { part: 100, side: 40, filter: 20 },
  wifiOn: true,
  targetsOn: true,
  zOffset: 0.0,
  moveStep: 1, // 0.1 | 1 | 10
  pos: { x: 120.0, y: 80.0, z: 0.2 },
  paused: false,
  selectedFile: 0,
  loadMode: "", // "" | "load" | "unload"
  loadStep: 0,  // 0=idle | 1=heating | 2=feeding | 3=done
  loadTarget: 240,
};

// Nav: ids por página — ver hmi/sk1-hmi.HMI.ids.json e bridge/sk1_hmi/ui/route.py
const NAV_PAGE_IDS = {
  home: { home: 1, print: 2, move: 3, files: 4, more: 5 },
  print: { home: 15, print: 16, move: 17, files: 18, more: 19 },
  move: { home: 21, print: 22, move: 23, files: 24, more: 25 },
  files: { home: 16, print: 17, move: 18, files: 19, more: 20 },
  fans: { home: 11, print: 12, move: 13, files: 14, more: 15 },
  load: { home: 1, print: 2, move: 3, files: 4, more: 5 },
};

function makeNav(activeObj, pageName = "home") {
  const ids = NAV_PAGE_IDS[pageName] || NAV_PAGE_IDS.home;
  const slots = [
    { slot: "home", obj: "nav_home", key: "home", x: 51, intent: "NavHome" },
    { slot: "move", obj: "nav_move", key: "move", x: 134, intent: "NavMove" },
    { slot: "files", obj: "nav_files", key: "files", x: 218, intent: "NavFiles" },
    { slot: "more", obj: "nav_more", key: "settings", x: 301, intent: "NavSettings" },
    { slot: "print", obj: "nav_print", key: "print", x: 373, intent: "NavPrint" },
  ];
  return slots.map((s) => {
    const isActive = s.obj === activeObj;
    return {
      id: ids[s.slot],
      obj: s.obj,
      type: "button",
      x: s.x,
      y: 234,
      w: 46,
      h: 36,
      sprite: `nav_${s.key}_${isActive ? "active" : "inactive"}`,
      className: `sprite-btn nav${isActive ? " active" : ""}`,
      intent: s.intent,
    };
  });
}

function getPages() {
  return {
    home: {
      id: 0,
      name: "home",
      bg: "../../assets/backgrounds/home.png",
      comps: [
        ...makeNav("nav_home", "home"),
        {
          id: 8,
          obj: "p_wifi",
          type: "button",
          x: 444,
          y: 6,
          w: 24,
          h: 21,
          sprite: sim.wifiOn ? "wifi_on" : "wifi_off",
          className: "sprite-btn status-icon",
          intent: "NavNetwork",
        },
        { id: 9, obj: "t_status", type: "text", x: 164, y: 8, w: 270, h: 16, text: "Standby", className: "status-left" },
        { id: 10, obj: "t_toolhead", type: "text", x: 355, y: 52, w: 104, h: 24, text: "34°C", className: "sensor-val" },
        { id: 11, obj: "t_mcu", type: "text", x: 356, y: 115, w: 104, h: 24, text: "38°C", className: "sensor-val" },
        { id: 12, obj: "t_chamber", type: "text", x: 356, y: 177, w: 104, h: 24, text: "29°C", className: "sensor-val" },
        { id: 13, obj: "t_hotend_tgt", type: "text", x: 13, y: 54, w: 56, h: 15, text: sim.targetsOn ? "220°C" : "", className: "temp-tgt" },
        { id: 14, obj: "t_hotend_dir", type: "text", x: 13, y: 71, w: 56, h: 13, text: sim.targetsOn ? "▲" : "", className: "temp-arrow" },
        { id: 15, obj: "t_hotend", type: "text", x: 13, y: 88, w: 56, h: 18, text: "25°C", className: "temp-stock" },
        { id: 19, obj: "t_hotend_lbl", type: "hotspot", x: 22, y: 120, w: 38, h: 38, text: "", className: "baked-hit", intent: "NavMove" },
        { id: 16, obj: "t_bed_tgt", type: "text", x: 73, y: 54, w: 56, h: 15, text: sim.targetsOn ? "60°C" : "", className: "temp-tgt" },
        { id: 17, obj: "t_bed_dir", type: "text", x: 73, y: 71, w: 56, h: 13, text: sim.targetsOn ? "▲" : "", className: "temp-arrow" },
        { id: 18, obj: "t_bed", type: "text", x: 73, y: 88, w: 56, h: 18, text: "25°C", className: "temp-stock" },
        { id: 20, obj: "t_bed_lbl", type: "hotspot", x: 81, y: 120, w: 38, h: 38, text: "", className: "baked-hit", intent: "NavMove" },
        {
          id: 6,
          obj: "b_light",
          type: "button",
          x: 3,
          y: 195,
          w: 70,
          h: 31,
          sprite: sim.lightOn ? "light_on" : "light_off",
          className: "sprite-btn",
          intent: "ToggleCaseLight",
        },
        {
          id: 7,
          obj: "b_fan",
          type: "button",
          x: 78,
          y: 195,
          w: 71,
          h: 31,
          sprite: sim.fanOn ? "fan_on" : "fan_off",
          className: "sprite-btn",
          intent: "TogglePartFan",
        },
      ],
    },

    print: {
      id: 1,
      name: "print",
      bg: "../../assets/backgrounds/print.png",
      comps: [
        // Nenhum ícone da barra inferior em highlight na tela Print
        ...makeNav(null, "print"),
        { id: 1, obj: "j_progress", type: "progress", x: 16, y: 74, w: 308, h: 8, val: 42 },
        {
          id: 2,
          obj: "p_wifi",
          type: "button",
          x: 444,
          y: 9,
          w: 24,
          h: 20,
          sprite: sim.wifiOn ? "wifi_on" : "wifi_off",
          className: "sprite-btn status-icon",
          intent: "NavNetwork",
        },
        { id: 3, obj: "p_thumb", type: "picture", x: 340, y: 48, w: 126, h: 116, text: "3D preview" },
        {
          id: 4,
          obj: "b_pause",
          type: "button",
          x: 340,
          y: 171,
          w: 59,
          h: 46,
          sprite: sim.paused ? "resume_btn" : "pause_btn",
          className: "sprite-btn",
          intent: "PauseOrResume",
        },
        {
          id: 5,
          obj: "b_cancel",
          type: "button",
          x: 407,
          y: 171,
          w: 59,
          h: 46,
          sprite: "cancel_btn",
          className: "sprite-btn",
          intent: "CancelPrint",
        },
        { id: 6, obj: "t_file", type: "text", x: 42, y: 11, w: 390, h: 22, text: "SK1_benchy_pla.gcode", icon: "print", className: "title" },
        { id: 7, obj: "t_progress", type: "text", x: 14, y: 46, w: 80, h: 24, text: "42%", className: "temp-amber" },
        { id: 8, obj: "t_hotend", type: "text", x: 44, y: 92, w: 122, h: 34, text: "210 / 220°C", icon: "nozzle", className: "temp-row" },
        { id: 9, obj: "t_bed", type: "text", x: 204, y: 92, w: 122, h: 34, text: "60 / 60°C", icon: "bed", className: "temp-row" },
        { id: 10, obj: "t_toolhead", type: "text", x: 50, y: 134, w: 58, h: 28, text: "34°C", className: "mini-temp" },
        { id: 11, obj: "t_mcu", type: "text", x: 156, y: 134, w: 58, h: 28, text: "38°C", className: "mini-temp" },
        { id: 12, obj: "t_chamber", type: "text", x: 262, y: 134, w: 58, h: 28, text: "29°C", className: "mini-temp" },
        { id: 13, obj: "t_z", type: "text", x: 128, y: 177, w: 136, h: 34, text: `${sim.zOffset >= 0 ? "+" : ""}${sim.zOffset.toFixed(3)} mm`, className: "z-val" },
        { id: 14, obj: "t_eta", type: "text", x: 100, y: 50, w: 224, h: 18, text: "ETA 00:38:12", className: "status" },
        {
          id: 21,
          obj: "b_z_m",
          type: "button",
          x: 68,
          y: 177,
          w: 50,
          h: 34,
          sprite: "z_step_minus_btn",
          className: "sprite-btn z-step",
          intent: "BabyStep(-0.025)",
        },
        {
          id: 22,
          obj: "b_z_p",
          type: "button",
          x: 268,
          y: 177,
          w: 50,
          h: 34,
          sprite: "z_step_plus_btn",
          className: "sprite-btn z-step",
          intent: "BabyStep(+0.025)",
        },
      ],
    },

    move: {
      id: 2,
      name: "move",
      bg: "../../assets/backgrounds/move.png",
      comps: [
        ...makeNav("nav_move", "move"),
        { id: 6, obj: "b_tab_move", type: "hotspot", x: 10, y: 2, w: 140, h: 30, text: "", className: "baked-hit", intent: "NavMove" },
        { id: 17, obj: "b_tab_load", type: "hotspot", x: 162, y: 2, w: 156, h: 30, text: "", className: "baked-hit", intent: "NavLoad" },
        { id: 18, obj: "b_tab_fan", type: "hotspot", x: 348, y: 2, w: 86, h: 30, text: "", className: "baked-hit", intent: "NavFans" },
        {
          id: 15,
          obj: "p_wifi",
          type: "button",
          x: 444,
          y: 6,
          w: 26,
          h: 21,
          sprite: sim.wifiOn ? "wifi_on" : "wifi_off",
          className: "sprite-btn status-icon",
          intent: "NavNetwork",
        },
        { id: 2, obj: "t_rail_hotend", type: "text", x: 50, y: 44, w: 46, h: 20, text: "25°C", className: "rail-val" },
        { id: 19, obj: "t_rail_bed", type: "text", x: 50, y: 111, w: 46, h: 20, text: "25°C", className: "rail-val" },
        { id: 20, obj: "t_rail_fan", type: "text", x: 50, y: 178, w: 46, h: 20, text: sim.fanOn ? "100%" : "OFF", className: "rail-val" },
        {
          id: 12,
          obj: "b_step_01",
          type: "button",
          x: 108,
          y: 39,
          w: 70,
          h: 34,
          sprite: sim.moveStep === 0.1 ? "step_01_active" : "step_01_inactive",
          className: "sprite-btn",
          intent: "SetMoveStep(0.1)",
        },
        {
          id: 13,
          obj: "b_step_1",
          type: "button",
          x: 180,
          y: 39,
          w: 70,
          h: 34,
          sprite: sim.moveStep === 1 ? "step_1_active" : "step_1_inactive",
          className: "sprite-btn",
          intent: "SetMoveStep(1)",
        },
        {
          id: 14,
          obj: "b_step_10",
          type: "button",
          x: 252,
          y: 39,
          w: 70,
          h: 34,
          sprite: sim.moveStep === 10 ? "step_10_active" : "step_10_inactive",
          className: "sprite-btn",
          intent: "SetMoveStep(10)",
        },
        {
          id: 16,
          obj: "b_step_30",
          type: "button",
          x: 324,
          y: 39,
          w: 70,
          h: 34,
          sprite: sim.moveStep === 30 ? "step_30_active" : "step_30_inactive",
          className: "sprite-btn",
          intent: "SetMoveStep(30)",
        },
        // D-pad XY (hitboxes estritamente disjuntas — zero sobreposição no TJC)
        { id: 3, obj: "b_y_p", type: "button", x: 216, y: 78, w: 60, h: 36, text: "", className: "baked-hit", intent: "MoveAxis Y+" },
        { id: 5, obj: "b_x_m", type: "button", x: 176, y: 116, w: 38, h: 58, text: "", className: "baked-hit", intent: "MoveAxis X-" },
        { id: 10, obj: "b_home_xy", type: "button", x: 220, y: 120, w: 52, h: 50, text: "", className: "baked-hit", intent: "HomeXY" },
        { id: 7, obj: "b_x_p", type: "button", x: 276, y: 116, w: 38, h: 58, text: "", className: "baked-hit", intent: "MoveAxis X+" },
        { id: 8, obj: "b_y_m", type: "button", x: 216, y: 176, w: 60, h: 36, text: "", className: "baked-hit", intent: "MoveAxis Y-" },
        { id: 4, obj: "b_z_p", type: "button", x: 407, y: 39, w: 60, h: 51, text: "", className: "baked-hit", intent: "MoveAxis Z+" },
        { id: 11, obj: "b_home_z", type: "button", x: 407, y: 102, w: 60, h: 51, text: "", className: "baked-hit", intent: "HomeZ" },
        { id: 9, obj: "b_z_m", type: "button", x: 407, y: 165, w: 60, h: 51, text: "", className: "baked-hit", intent: "MoveAxis Z-" },
        { id: 1, obj: "t_pos", type: "text", x: 108, y: 215, w: 190, h: 14, text: `X${sim.pos.x.toFixed(1)} Y${sim.pos.y.toFixed(1)} Z${sim.pos.z.toFixed(2)}`, className: "muted" },
      ],
    },

    files: {
      id: 3,
      name: "files",
      bg: "../../assets/backgrounds/files.png",
      comps: [
        ...makeNav("nav_files", "files"),
        { id: 1, obj: "t_title", type: "text", x: 42, y: 11, w: 200, h: 22, text: "Files", icon: "files", className: "title" },
        ...[
          "benchy_pla_220.gcode",
          "calibration_cube.gcode",
          "spiral_vase_petg.gcode",
          "fan_duct_abs.gcode",
          "first_layer_test.gcode",
        ].map((fname, idx) => ({
          id: 2 + idx,
          obj: `t_f${idx}`,
          type: "text",
          x: 20,
          y: 54 + idx * 33,
          w: 290,
          h: 28,
          text: `${sim.selectedFile === idx ? "> " : "  "}${fname}`,
          className: `file-row${sim.selectedFile === idx ? " selected-file" : ""}`,
        })),
        ...[0, 1, 2, 3, 4].map((idx) => ({
          id: 8 + idx,
          obj: `b_f${idx}`,
          type: "hotspot",
          x: 18,
          y: 52 + idx * 33,
          w: 294,
          h: 30,
          text: "",
          className: "baked-hit",
          intent: `SelectFile(${idx})`,
        })),
        { id: 7, obj: "p_thumb", type: "picture", x: 334, y: 52, w: 128, h: 100, text: "gcode thumb" },
        {
          id: 13,
          obj: "b_up",
          type: "button",
          x: 332,
          y: 164,
          w: 62,
          h: 24,
          sprite: "files_up_btn",
          className: "sprite-btn",
          intent: "FilesPageUp",
        },
        {
          id: 14,
          obj: "b_down",
          type: "button",
          x: 402,
          y: 164,
          w: 62,
          h: 24,
          sprite: "files_down_btn",
          className: "sprite-btn",
          intent: "FilesPageDown",
        },
        {
          id: 15,
          obj: "b_print",
          type: "button",
          x: 332,
          y: 192,
          w: 132,
          h: 28,
          sprite: "files_print_btn",
          className: "sprite-btn",
          intent: "StartSelectedFile",
        },
      ],
    },

    fans: {
      id: 4,
      name: "fans",
      bg: "../../assets/backgrounds/fans.png",
      comps: [
        ...makeNav("nav_move", "fans"),
        { id: 1, obj: "b_tab_move", type: "hotspot", x: 10, y: 2, w: 140, h: 30, text: "", className: "baked-hit", intent: "NavMove" },
        { id: 2, obj: "b_tab_load", type: "hotspot", x: 162, y: 2, w: 156, h: 30, text: "", className: "baked-hit", intent: "NavLoad" },
        { id: 3, obj: "b_tab_fan", type: "hotspot", x: 330, y: 2, w: 100, h: 30, text: "", className: "baked-hit", intent: "NavFans" },
        {
          id: 4,
          obj: "p_wifi",
          type: "button",
          x: 444,
          y: 6,
          w: 22,
          h: 18,
          sprite: sim.wifiOn ? "wifi_on" : "wifi_off",
          className: "sprite-btn status-icon",
          intent: "NavNetwork",
        },
        { id: 5, obj: "t_part", type: "text", x: 394, y: 48, w: 62, h: 18, text: `${sim.fans.part}%`, className: "mini-temp" },
        { id: 8, obj: "h_part", type: "slider", x: 68, y: 67, w: 388, h: 28, val: sim.fans.part, targetText: "t_part", fanKey: "part", intent: "SetPartFan" },
        { id: 6, obj: "t_side", type: "text", x: 394, y: 110, w: 62, h: 18, text: `${sim.fans.side}%`, className: "mini-temp" },
        { id: 9, obj: "h_side", type: "slider", x: 68, y: 129, w: 388, h: 28, val: sim.fans.side, targetText: "t_side", fanKey: "side", intent: "SetSideFan" },
        { id: 7, obj: "t_filter", type: "text", x: 394, y: 172, w: 62, h: 18, text: `${sim.fans.filter}%`, className: "mini-temp" },
        { id: 10, obj: "h_filter", type: "slider", x: 68, y: 191, w: 388, h: 28, val: sim.fans.filter, targetText: "t_filter", fanKey: "filter", intent: "SetFilterFan" },
      ],
    },

    load: {
      id: 5,
      name: "load",
      bg: "../../assets/backgrounds/load.png",
      comps: [
        ...makeNav("nav_move"),
        { id: 25, obj: "b_tab_move", type: "hotspot", x: 10, y: 2, w: 140, h: 30, text: "", className: "baked-hit", intent: "NavMove" },
        { id: 28, obj: "b_tab_load", type: "hotspot", x: 162, y: 2, w: 156, h: 30, text: "", className: "baked-hit", intent: "NavLoad" },
        { id: 26, obj: "b_tab_fan", type: "hotspot", x: 330, y: 2, w: 100, h: 30, text: "", className: "baked-hit", intent: "NavFans" },
        {
          id: 23,
          obj: "p_wifi",
          type: "button",
          x: 444,
          y: 6,
          w: 22,
          h: 18,
          sprite: sim.wifiOn ? "wifi_on" : "wifi_off",
          className: "sprite-btn status-icon",
          intent: "NavNetwork",
        },
        // Painel esquerdo — stepper 1-2-3
        {
          id: 6,
          obj: "t_mode",
          type: "text",
          x: 16,
          y: 46,
          w: 142,
          h: 20,
          text: sim.loadMode === "load" ? "Load" : sim.loadMode === "unload" ? "Unload" : "Load/Unload",
          className: "load-mode",
        },
        {
          id: 7,
          obj: "t_step1",
          type: "text",
          x: 45,
          y: 84,
          w: 112,
          h: 20,
          text: "Heating",
          className: `load-step${sim.loadStep === 1 ? " active" : sim.loadStep > 1 ? " done" : ""}`,
        },
        {
          id: 8,
          obj: "t_step2",
          type: "text",
          x: 45,
          y: 129,
          w: 112,
          h: 20,
          text: sim.loadMode === "unload" ? "Unload..." : "Load...",
          className: `load-step${sim.loadStep === 2 ? " active" : sim.loadStep > 2 ? " done" : ""}`,
        },
        {
          id: 9,
          obj: "t_step3",
          type: "text",
          x: 45,
          y: 174,
          w: 112,
          h: 20,
          text: sim.loadMode === "unload" ? "Return completed" : "Completed",
          className: `load-step${sim.loadStep === 3 ? " active" : ""}`,
        },
        // Painel direito — estado idle (seletor de temperatura) OU estado ativo (aquecendo / executando)
        ...(sim.loadStep === 0
          ? [
              { id: 14, obj: "t_temp_lbl", type: "text", x: 204, y: 56, w: 230, h: 22, text: "Nozzle temperature", className: "load-temp-title" },
              { id: 15, obj: "b_temp_m", type: "button", x: 204, y: 88, w: 46, h: 38, sprite: "temp_left_btn", className: "sprite-btn", intent: "LoadTempStep(-10)" },
              { id: 16, obj: "t_set_temp", type: "text", x: 262, y: 88, w: 114, h: 38, text: `${sim.loadTarget}°C`, className: "load-temp-box" },
              { id: 17, obj: "b_temp_p", type: "button", x: 388, y: 88, w: 46, h: 38, sprite: "temp_right_btn", className: "sprite-btn", intent: "LoadTempStep(+10)" },
            ]
          : [
              { id: 18, obj: "p_nozzle", type: "picture", x: 289, y: 50, w: 60, h: 62, sprite: "nozzle_therm" },
              { id: 10, obj: "t_hotend", type: "text", x: 194, y: 116, w: 94, h: 24, text: `${sim.loadStep === 1 ? Math.max(25, sim.loadTarget - 30) : sim.loadTarget}°C`, className: "load-temp-read" },
              { id: 19, obj: "p_arrow", type: "picture", x: 307, y: 120, w: 24, h: 16, sprite: "temp_arrow" },
              { id: 11, obj: "t_hotend_tgt", type: "text", x: 350, y: 116, w: 94, h: 24, text: `${sim.loadTarget}°C`, className: "load-temp-read" },
            ]),
        {
          id: 12,
          obj: "b_load",
          type: "button",
          x: 204,
          y: 158,
          w: 100,
          h: 38,
          sprite: sim.loadMode === "load" && sim.loadStep > 0 ? "load_active" : "load_inactive",
          className: "sprite-btn",
          intent: "LoadFilament",
        },
        {
          id: 13,
          obj: "b_unload",
          type: "button",
          x: 334,
          y: 158,
          w: 100,
          h: 38,
          sprite: sim.loadMode === "unload" && sim.loadStep > 0 ? "unload_active" : "unload_inactive",
          className: "sprite-btn",
          intent: "UnloadFilament",
        },
      ],
    },
    zoffset: stubPage(6, "zoffset", "Z-Offset", "../../assets/backgrounds/zoffset.png"),
    calibrate: stubPage(7, "calibrate", "Calibrate", "../../assets/backgrounds/calibrate.png"),
    network: {
      id: 8,
      name: "network",
      bg: "../../assets/backgrounds/network.png",
      comps: [
        ...makeNav(""),
        {
          id: 6,
          obj: "t_ip",
          type: "text",
          x: 192,
          y: 131,
          w: 160,
          h: 30,
          text: "192.168.0.17",
          className: "title",
        },
      ],
    },
    settings: stubPage(9, "settings", "Settings", "../../assets/backgrounds/settings.png", "more"),
  };
}

function stubPage(id, name, title, bg, icon) {
  const activeNav = name === "settings" ? "nav_more" : "";
  return {
    id,
    name,
    bg,
    comps: [
      ...makeNav(activeNav),
      { id: 10, obj: "t_title", type: "text", x: 16, y: 9, w: 220, h: 24, text: title, icon, className: "title" },
      { id: 11, obj: "t_info", type: "text", x: 26, y: 66, w: 420, h: 32, text: `Tela ${title} — tema charcoal + amber glow`, className: "muted" },
      { id: 12, obj: "b_stub", type: "button", x: 26, y: 118, w: 140, h: 42, text: "Action", className: "cta primary", intent: "StubAction" },
    ],
  };
}

const pageOrder = ["home", "print", "move", "files", "fans", "load", "zoffset", "calibrate", "network", "settings"];
let current = "home";
let selected = null;

const tabsEl = document.getElementById("tabs");
const screenEl = document.getElementById("screen");
const inspectorEl = document.getElementById("inspector");
const listEl = document.getElementById("comp-list");
const chkGuides = document.getElementById("chk-guides");
const chkLabels = document.getElementById("chk-labels");
const chkTargets = document.getElementById("chk-targets");

function iconUrl(name) {
  return `${ICON_BASE}/${name}.png?v=${VER}`;
}
function spriteUrl(name) {
  return `${UI_BASE}/${name}.png?v=${VER}`;
}

function fillContent(node, comp) {
  node.replaceChildren();
  if (comp.type === "slider") {
    const inp = document.createElement("input");
    inp.type = "range";
    inp.min = "0";
    inp.max = "100";
    inp.value = String(comp.val ?? 0);
    inp.style.setProperty("--pct", `${comp.val ?? 0}%`);
    inp.addEventListener("input", (ev) => {
      ev.stopPropagation();
      const v = Number(inp.value);
      inp.style.setProperty("--pct", `${v}%`);
      comp.val = v;
      if (comp.fanKey) {
        sim.fans[comp.fanKey] = v;
        if (comp.fanKey === "part") sim.fanOn = v > 0;
      }
      if (comp.targetText) {
        const txtNode = screenEl.querySelector(`.comp[data-obj="${comp.targetText}"] .lbl`);
        if (txtNode) txtNode.textContent = `${v}%`;
      }
      selectComp(comp);
    });
    node.appendChild(inp);
    return;
  }
  if (comp.type === "progress") {
    const bar = document.createElement("i");
    bar.style.width = `${comp.val || 0}%`;
    node.appendChild(bar);
    return;
  }
  if (comp.sprite) {
    const img = document.createElement("img");
    img.className = "sprite";
    img.src = spriteUrl(comp.sprite);
    img.alt = comp.obj;
    img.draggable = false;
    node.appendChild(img);
    return;
  }
  if (comp.icon) {
    const img = document.createElement("img");
    img.className = "ico";
    const titleIco =
      comp.className?.includes("title") &&
      (comp.icon === "print" || comp.icon === "files");
    const tempIco =
      comp.className?.includes("temp-row") &&
      (comp.icon === "nozzle" || comp.icon === "bed");
    const tempName =
      comp.icon === "nozzle" ? "print_temp_nozzle" : "print_temp_bed";
    img.src = titleIco
      ? spriteUrl(`title_${comp.icon}`)
      : tempIco
        ? spriteUrl(tempName)
        : iconUrl(comp.icon);
    img.alt = "";
    img.draggable = false;
    node.appendChild(img);
  }
  if (comp.text != null && comp.text !== "") {
    const span = document.createElement("span");
    span.className = "lbl";
    span.textContent = comp.text;
    node.appendChild(span);
  }
}

function handleAction(comp) {
  if (!comp.intent) return;
  if (comp.intent.startsWith("Nav")) {
    const map = {
      NavHome: "home",
      NavPrint: "print",
      NavMove: "move",
      NavFiles: "files",
      NavFans: "fans",
      NavLoad: "load",
      NavSettings: "settings",
      NavNetwork: "network",
    };
    if (map[comp.intent]) {
      if (comp.intent === "NavLoad" && sim.loadStep === 3) {
        sim.loadStep = 0;
        sim.loadMode = "";
      }
      show(map[comp.intent]);
      return;
    }
  }
  if (comp.intent.startsWith("LoadTempStep(")) {
    const delta = parseInt(comp.intent.slice(13, -1), 10);
    sim.loadTarget = Math.max(170, Math.min(300, sim.loadTarget + delta));
    show(current, comp.obj);
    return;
  }
  if (comp.intent === "LoadFilament" || comp.intent === "UnloadFilament") {
    const nextMode = comp.intent === "LoadFilament" ? "load" : "unload";
    if (sim.loadMode === nextMode && sim.loadStep > 0) {
      sim.loadStep = sim.loadStep >= 3 ? 0 : sim.loadStep + 1;
      if (sim.loadStep === 0) sim.loadMode = "";
    } else {
      sim.loadMode = nextMode;
      sim.loadStep = 1;
    }
    show(current, comp.obj);
    return;
  }
  if (comp.intent === "ToggleCaseLight") {
    sim.lightOn = !sim.lightOn;
    show(current, comp.obj);
    return;
  }
  if (comp.intent === "TogglePartFan") {
    sim.fanOn = !sim.fanOn;
    show(current, comp.obj);
    return;
  }
  if (comp.intent === "ToggleWifiMock") {
    sim.wifiOn = !sim.wifiOn;
    show(current, comp.obj);
    return;
  }
  if (comp.intent === "PauseOrResume") {
    sim.paused = !sim.paused;
    show(current, comp.obj);
    return;
  }
  if (comp.intent.startsWith("BabyStep(")) {
    const delta = parseFloat(comp.intent.slice(9, -1));
    sim.zOffset = +(sim.zOffset + delta).toFixed(3);
    show(current, comp.obj);
    return;
  }
  if (comp.intent.startsWith("SetMoveStep(")) {
    sim.moveStep = parseFloat(comp.intent.slice(12, -1));
    show(current, comp.obj);
    return;
  }
  if (comp.intent.startsWith("MoveAxis ")) {
    const ax = comp.intent.slice(9);
    const axis = ax[0].toLowerCase();
    const dir = ax[1] === "+" ? 1 : -1;
    sim.pos[axis] = Math.max(0, +(sim.pos[axis] + dir * sim.moveStep).toFixed(2));
    show(current, comp.obj);
    return;
  }
  if (comp.intent === "HomeXY") {
    sim.pos.x = 0;
    sim.pos.y = 0;
    show(current, comp.obj);
    return;
  }
  if (comp.intent === "HomeZ") {
    sim.pos.z = 0;
    show(current, comp.obj);
    return;
  }
  if (comp.intent.startsWith("SelectFile(")) {
    sim.selectedFile = parseInt(comp.intent.slice(11, -1), 10);
    show(current, comp.obj);
  }
}

function elFor(comp) {
  const isBtn = comp.type === "button" || comp.type === "hotspot";
  const node = document.createElement(isBtn ? "button" : "div");
  node.className = `comp ${comp.className || ""}`.trim();
  if (comp.icon) node.classList.add("has-icon");
  node.dataset.obj = comp.obj;
  node.dataset.id = String(comp.id);
  node.dataset.type = comp.type;
  if (comp.intent) node.dataset.intent = comp.intent;
  node.style.left = `${comp.x}px`;
  node.style.top = `${comp.y}px`;
  node.style.width = `${comp.w}px`;
  node.style.height = `${comp.h}px`;
  fillContent(node, comp);
  node.addEventListener("click", (ev) => {
    ev.stopPropagation();
    selectComp(comp);
    handleAction(comp);
  });
  return node;
}

function selectComp(comp) {
  selected = comp;
  [...screenEl.querySelectorAll(".comp")].forEach((n) => {
    n.classList.toggle("selected", n.dataset.obj === comp.obj && n.dataset.id === String(comp.id));
  });
  inspectorEl.innerHTML = `
    <dl>
      <dt>page</dt><dd>${current} (#${getPages()[current].id})</dd>
      <dt>id</dt><dd>${comp.id}</dd>
      <dt>objname</dt><dd>${comp.obj}</dd>
      <dt>type</dt><dd>${comp.type}</dd>
      <dt>geom</dt><dd>${comp.x},${comp.y} ${comp.w}×${comp.h}</dd>
      <dt>intent</dt><dd>${comp.intent || "—"}</dd>
      <dt>sprite</dt><dd>${comp.sprite || comp.icon || "—"}</dd>
      <dt>txt/val</dt><dd>${comp.text ?? comp.val ?? "—"}</dd>
      <dt>bridge</dt><dd>${current}.${comp.obj}.txt=…</dd>
    </dl>
  `;
  [...listEl.children].forEach((li) => {
    li.classList.toggle("active", li.dataset.obj === comp.obj);
  });
}

function show(name, keepSelectedObj = null) {
  current = name;
  selected = null;
  [...tabsEl.children].forEach((b) => b.classList.toggle("active", b.dataset.page === name));
  const page = getPages()[name];
  screenEl.style.backgroundImage = `url("${page.bg}?v=${VER}")`;
  screenEl.innerHTML = "";
  page.comps.forEach((c) => screenEl.appendChild(elFor(c)));
  listEl.innerHTML = "";
  page.comps.forEach((c) => {
    const li = document.createElement("li");
    const tag = c.sprite ? ` [${c.sprite}]` : c.icon ? ` [${c.icon}]` : "";
    li.textContent = `#${c.id} ${c.obj}${tag}  ${c.x},${c.y} ${c.w}×${c.h}`;
    li.dataset.obj = c.obj;
    li.onclick = () => selectComp(c);
    listEl.appendChild(li);
  });
  if (keepSelectedObj) {
    const found = page.comps.find((c) => c.obj === keepSelectedObj);
    if (found) selectComp(found);
  } else {
    inspectorEl.innerHTML = `<p class="meta">Clique um componente na tela ou na lista.</p>`;
  }
  document.getElementById("page-meta").textContent =
    `${page.name} · page id ${page.id} · ${W}×${H} · ${page.comps.length} comps`;
}

chkGuides.addEventListener("change", () => {
  screenEl.classList.toggle("show-guides", chkGuides.checked);
});
chkLabels.addEventListener("change", () => {
  screenEl.classList.toggle("show-labels", chkLabels.checked);
});
chkTargets.addEventListener("change", () => {
  sim.targetsOn = chkTargets.checked;
  show(current, selected ? selected.obj : null);
});
screenEl.addEventListener("click", () => {
  selected = null;
  [...screenEl.querySelectorAll(".comp")].forEach((n) => n.classList.remove("selected"));
  inspectorEl.innerHTML = `<p class="meta">Nenhum componente selecionado.</p>`;
});

pageOrder.forEach((name) => {
  const b = document.createElement("button");
  b.textContent = name;
  b.dataset.page = name;
  b.onclick = () => show(name);
  tabsEl.appendChild(b);
});

chkGuides.checked = false;
show("home");
