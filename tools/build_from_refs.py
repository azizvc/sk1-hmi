#!/usr/bin/env python3
"""
Build 480x272 clean backgrounds and cropped/synthesized state sprites
from the two SK1 stock reference screenshots.

Outputs:
  assets/backgrounds/*.png  (480x272 RGB)
  assets/ui/*.png           (cropped & state sprites RGBA)
  hmi/images/*.png          (synced copy for USART HMI / preview)
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG_DIR = ROOT / "assets" / "backgrounds"
UI_DIR = ROOT / "assets" / "ui"
ICON_DIR = ROOT / "assets" / "icons"
HMI_IMG_DIR = ROOT / "hmi" / "images"

REF_HOME = Path(
    r"C:\Users\aziz\.cursor\projects\c-Users-aziz-Desktop-sk1-hmi\assets\image-ed19f0dc-f2c9-4d1e-82ae-3ffb2546c086.png"
)
REF_MOVE = Path(
    r"C:\Users\aziz\.cursor\projects\c-Users-aziz-Desktop-sk1-hmi\assets\image-b838c41b-ad83-4774-927d-063785f79200.png"
)

W, H = 480, 272
REF_W, REF_H = 1024, 572

# Exact palette sampled from stock references
BG_MAIN = (23, 23, 23)
BG_PANEL = (31, 31, 31)
BG_NAV = (20, 20, 20)
BG_WELL = (24, 24, 26)
AMBER = (255, 153, 0)
AMBER_BRIGHT = (255, 178, 36)
AMBER_DIM = (155, 105, 42)
MUTED = (128, 126, 120)
LINE_DARK = (46, 42, 36)
LINE_AMBER = (105, 78, 42)
TEXT_LIGHT = (240, 226, 198)
DANGER = (212, 91, 74)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for p in candidates:
        fp = Path(p)
        if fp.exists():
            return ImageFont.truetype(str(fp), size)
    return ImageFont.load_default()


def sx(x: float) -> int:
    return round(x * W / REF_W)


def sy(y: float) -> int:
    return round(y * H / REF_H)


def clean_nav_bar(arr: np.ndarray, nav_bg: tuple[int, int, int]) -> None:
    """Erase all 5 nav icons/glows below the y=488 divider line (in 1024x572 coords)."""
    arr[489:, :, :] = nav_bg


def draw_home_sensor_icon(img: Image.Image, kind: str, box: tuple[int, int, int, int]) -> None:
    """Draw amber icon well + vector glyph for Toolhead, MCU, Chamber."""
    draw_glow_box(img, box, radius=8, fill=BG_WELL, outline=AMBER, glow_alpha=45, width=1)
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    d = ImageDraw.Draw(img)
    col = AMBER_BRIGHT
    dim = AMBER_DIM

    if kind == "toolhead":
        # Hotend carriage / toolhead PCB + nozzle tip
        d.rounded_rectangle((cx - 8, cy - 9, cx + 8, cy + 2), radius=2, outline=col, width=2)
        d.line((cx - 4, cy - 4, cx + 4, cy - 4), fill=dim, width=1)
        d.polygon([(cx - 5, cy + 2), (cx + 5, cy + 2), (cx, cy + 10)], outline=col, fill=None)
        d.line((cx - 4, cy + 3, cx + 4, cy + 3), fill=col, width=1)
    elif kind == "mcu":
        # IC chip + pins on all 4 sides
        d.rounded_rectangle((cx - 6, cy - 6, cx + 6, cy + 6), radius=2, outline=col, width=2)
        d.rectangle((cx - 2, cy - 2, cx + 2, cy + 2), fill=col)
        for off in (-4, 0, 4):
            d.line((cx + off, cy - 10, cx + off, cy - 7), fill=col, width=1)
            d.line((cx + off, cy + 7, cx + off, cy + 10), fill=col, width=1)
            d.line((cx - 10, cy + off, cx - 7, cy + off), fill=col, width=1)
            d.line((cx + 7, cy + off, cx + 10, cy + off), fill=col, width=1)
    elif kind == "chamber":
        # Enclosure cube + thermometer/heat wave inside
        d.rounded_rectangle((cx - 9, cy - 8, cx + 9, cy + 8), radius=2, outline=col, width=2)
        d.line((cx - 9, cy - 4, cx + 9, cy - 4), fill=dim, width=1)
        for dx in (-4, 0, 4):
            d.arc((cx + dx - 2, cy - 1, cx + dx + 2, cy + 5), start=90, end=270, fill=col, width=1)


def build_home_bg(h0: np.ndarray) -> Image.Image:
    """Clean home background at 1024x572 then downsample cleanly to 480x272."""
    arr = h0.copy()

    # 1. Erase dynamic "25°C" / "25°C" readouts above the two wells
    # Left panel flat background is [31, 31, 31]
    arr[198:240, 35:305] = BG_PANEL

    # 2. Erase Light & Fan buttons (replaced by light_on/off and fan_on/off sprites)
    # Keep the top horizontal divider at y=402..406 intact; clean below y=408 inside left panel
    arr[408:482, 0:323] = BG_PANEL

    # 3. Replace right-side temperature graph (x=327..1024, y=0..484) with clean dark panel
    # Vertical amber divider sits at x=323..326; keep it and bottom divider (y=485..488) intact
    arr[0:485, 327:1024] = BG_MAIN

    # 4. Clean bottom nav icons (below y=489)
    clean_nav_bar(arr, BG_NAV)

    img = Image.fromarray(arr).resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")

    # 5. Draw 3 right-side sensor cards (Toolhead, MCU, Chamber) at 480x272 resolution
    # Right pane usable area: x=156..478, y=0..227 (top header y=4..28 holds t_status + p_wifi)
    d = ImageDraw.Draw(img)
    d.line((164, 31, 470, 31), fill=LINE_DARK + (255,), width=1)

    lbl_font = load_font(12, bold=True)
    sub_font = load_font(9, bold=False)

    cards = [
        ("toolhead", "Toolhead", "Extruder PCB", 38),
        ("mcu", "MCU", "Mainboard", 100),
        ("chamber", "Chamber", "Enclosure", 162),
    ]
    for kind, title, sub, y0 in cards:
        y1 = y0 + 54
        draw_glow_box(img, (164, y0, 470, y1), radius=9, fill=(26, 26, 28), outline=LINE_AMBER, glow_alpha=24, width=1)
        draw_home_sensor_icon(img, kind, (174, y0 + 9, 210, y0 + 45))
        d = ImageDraw.Draw(img)
        d.text((222, y0 + 11), title, fill=TEXT_LIGHT + (255,), font=lbl_font)
        d.text((222, y0 + 29), sub, fill=MUTED + (255,), font=sub_font)

    return img.convert("RGB")


def build_move_bg(m0: np.ndarray) -> Image.Image:
    """Clean move background at 1024x572 then downsample cleanly to 480x272."""
    arr = m0.copy()

    # 1. Erase top-right wifi + ! badge in header (x=936..1024, y=0..72)
    # Sample clean header background strip from x=710..798 (gap between Load/Unload and Fan)
    hdr_strip = arr[0:72, 710:798].copy()
    arr[0:72, 936:1024] = hdr_strip

    # 2. Erase left rail dynamic values ("25°C", "25°C", "OFF")
    # Keep the left icon wells (x=15..98) and horizontal dividers
    arr[92:138, 106:204] = BG_MAIN
    arr[230:276, 106:204] = BG_MAIN
    arr[376:424, 106:204] = BG_MAIN

    # 3. Erase all 3 step pills (1mm, 10mm, 30mm) so step sprites swap cleanly
    arr[70:162, 238:838] = BG_MAIN

    # 4. Clean bottom nav icons (below y=489)
    clean_nav_bar(arr, (21, 21, 21))

    img = Image.fromarray(arr).resize((W, H), Image.Resampling.LANCZOS)
    return img.convert("RGB")


def draw_glow_box(
    base: Image.Image,
    box: tuple[int, int, int, int],
    radius: int = 8,
    fill: tuple[int, int, int] = BG_WELL,
    outline: tuple[int, int, int] = AMBER,
    glow_alpha: int = 60,
    width: int = 1,
) -> None:
    x0, y0, x1, y1 = box
    if glow_alpha > 0:
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        pad = 4
        ld.rounded_rectangle(
            (x0 - pad, y0 - pad, x1 + pad, y1 + pad),
            radius=radius + 3,
            fill=AMBER + (glow_alpha,),
        )
        layer = layer.filter(ImageFilter.GaussianBlur(radius=4))
        base.alpha_composite(layer)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box, radius=radius, fill=fill + (255,), outline=outline + (255,), width=width)


def make_stock_shell_bg(active_tab: str = "") -> Image.Image:
    """Create a cohesive 480x272 charcoal+amber stock background for secondary pages."""
    img = Image.new("RGBA", (W, H), BG_MAIN + (255,))
    d = ImageDraw.Draw(img)

    # Top header bar (matches move.png y=0..40)
    d.rectangle((0, 0, W, 40), fill=(16, 16, 16, 255))
    # Subtle warm right-side header gradient like Move/Temp header
    for x in range(152, W):
        t = (x - 152) / (W - 152)
        c = (int(18 + 18 * t), int(16 + 11 * t), int(14 + 4 * t), 255)
        d.line((x, 0, x, 39), fill=c)
    d.line((0, 40, W, 40), fill=LINE_AMBER + (255,), width=1)

    # Bottom nav bar (matches home.png & move.png y=230..272)
    d.line((0, 230, W, 230), fill=LINE_AMBER + (255,), width=1)
    d.rectangle((0, 231, W, H), fill=BG_NAV + (255,))
    return img


def build_print_bg() -> Image.Image:
    img = make_stock_shell_bg()
    # Progress bar slot
    draw_glow_box(img, (14, 72, 326, 84), radius=6, fill=(18, 18, 20), outline=LINE_DARK, glow_alpha=0, width=1)
    # Main hotend & bed wells
    draw_glow_box(img, (14, 92, 166, 126), radius=8, fill=(24, 24, 26), outline=LINE_DARK, glow_alpha=20, width=1)
    draw_glow_box(img, (174, 92, 326, 126), radius=8, fill=(24, 24, 26), outline=LINE_DARK, glow_alpha=20, width=1)
    # Secondary sensor mini-cards: Toolhead, MCU, Chamber
    sub_fnt = load_font(9, bold=True)
    sensors = [
        ("Tool", (14, 133, 114, 163)),
        ("MCU", (120, 133, 220, 163)),
        ("Chm", (226, 133, 326, 163)),
    ]
    for lbl, box in sensors:
        draw_glow_box(img, box, radius=7, fill=(22, 22, 24), outline=LINE_DARK, glow_alpha=12, width=1)
        d = ImageDraw.Draw(img)
        d.text((box[0] + 8, box[1] + 9), lbl, fill=MUTED + (255,), font=sub_fnt)
    # Fine Z-offset card (bottom left)
    draw_glow_box(img, (14, 171, 326, 217), radius=9, fill=(22, 22, 24), outline=LINE_AMBER, glow_alpha=20, width=1)
    d = ImageDraw.Draw(img)
    d.text((24, 188), "Z-OFF", fill=MUTED + (255,), font=sub_fnt)
    # Right column thumbnail well (above icon-only Pause / Cancel)
    draw_glow_box(img, (340, 48, 466, 164), radius=10, fill=(20, 20, 22), outline=AMBER_DIM, glow_alpha=40, width=1)
    return img.convert("RGB")


def build_print_action_sprites() -> None:
    """Icon-only 59x46 sprites for Print screen: pause, resume, and red rounded-square cancel."""
    w, h = 59, 46

    def make_base(outline_rgb: tuple[int, int, int], glow_rgb: tuple[int, int, int]) -> Image.Image:
        base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.rounded_rectangle((3, 3, w - 4, h - 4), radius=10, fill=glow_rgb + (85,))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=3))
        base.alpha_composite(glow)
        d = ImageDraw.Draw(base)
        d.rounded_rectangle((4, 4, w - 5, h - 5), radius=9, fill=(28, 28, 30, 255), outline=outline_rgb + (255,), width=1)
        return base

    # Pause: two glowing amber vertical bars
    pause = make_base(AMBER, AMBER)
    pd = ImageDraw.Draw(pause)
    pd.rounded_rectangle((20, 14, 26, 32), radius=2, fill=AMBER_BRIGHT + (255,))
    pd.rounded_rectangle((33, 14, 39, 32), radius=2, fill=AMBER_BRIGHT + (255,))
    pause.save(UI_DIR / "pause_btn.png")

    # Resume: glowing amber play triangle
    resume = make_base(AMBER, AMBER)
    rd = ImageDraw.Draw(resume)
    rd.polygon([(22, 13), (22, 33), (40, 23)], fill=AMBER_BRIGHT + (255,))
    resume.save(UI_DIR / "resume_btn.png")

    # Cancel: red rounded square icon
    red = (218, 72, 62)
    red_bright = (238, 92, 82)
    cancel = make_base(red, red)
    cd = ImageDraw.Draw(cancel)
    cd.rounded_rectangle((20, 14, 39, 32), radius=4, fill=red_bright + (255,))
    cancel.save(UI_DIR / "cancel_btn.png")


def build_files_bg() -> Image.Image:
    img = make_stock_shell_bg()
    # Left 5-row file list container
    draw_glow_box(img, (14, 50, 316, 218), radius=10, fill=(20, 20, 22), outline=LINE_DARK, glow_alpha=20, width=1)
    d = ImageDraw.Draw(img)
    for row in range(1, 5):
        ry = 50 + row * 33
        d.line((24, ry, 306, ry), fill=(36, 34, 32, 255), width=1)
    # Right thumbnail well
    draw_glow_box(img, (332, 50, 464, 154), radius=10, fill=(20, 20, 22), outline=AMBER_DIM, glow_alpha=40, width=1)
    return img.convert("RGB")


def draw_fan_glyph(img: Image.Image, box: tuple[int, int, int, int]) -> None:
    """Small glowing amber fan icon inside a rounded well."""
    draw_glow_box(img, box, radius=7, fill=BG_WELL, outline=AMBER, glow_alpha=36, width=1)
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    d = ImageDraw.Draw(img)
    col = AMBER_BRIGHT
    # 3 blades around center hub
    import math
    for deg in (-90, 30, 150):
        a = math.radians(deg)
        bx = cx + int(round(5.5 * math.cos(a)))
        by = cy + int(round(5.5 * math.sin(a)))
        d.ellipse((bx - 4, by - 4, bx + 4, by + 4), outline=col, width=1)
    d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=col)


def build_fans_bg(m0: np.ndarray) -> Image.Image:
    """Stock-styled Fans page with exact Move/Temp header tabs (Fan active) + 3 fan slider cards."""
    # 1. Start from exact 1024-wide header of m0 (y=0..66) and swap active state from tab 1 to tab 3
    hdr = m0[0:66, 0:1024].copy().astype(np.float32)

    # Clean Wi-Fi + alert in top-right (x=936..1024) using tab 3 bg [37,37,37]
    hdr[0:62, 936:1024] = m0[0:62, 710:798]

    # Tab 1 (Move/Temp, x=0..341): switch active bg [23,23,23] -> inactive [37,37,37] + muted text
    t1 = hdr[0:63, 0:341]
    alpha1 = np.clip(np.max(t1 - 23.0, axis=2) / (230.0 - 23.0), 0.0, 1.0)
    bg_inact = np.array([37.0, 37.0, 37.0])
    fg_muted = np.array([145.0, 118.0, 96.0])
    hdr[0:60, 0:341] = bg_inact + alpha1[0:60, :, None] * (fg_muted - bg_inact)
    # Match bottom edge line of inactive tabs (y=60..62 from tab 2 col 400)
    hdr[60:63, 0:341] = hdr[60:63, 400:401]

    # Tab 3 (Fan, x=682..1024): switch inactive bg [37,37,37] -> active [23,23,23] + bright text
    t3 = hdr[0:63, 682:1024]
    alpha3 = np.clip(np.max(t3 - 37.0, axis=2) / (145.0 - 37.0), 0.0, 1.0)
    bg_act = np.array([23.0, 23.0, 23.0])
    fg_bright = np.array([243.0, 205.0, 166.0])
    hdr[0:63, 682:1024] = bg_act + alpha3[:, :, None] * (fg_bright - bg_act)
    # Tab divider line between Load/Unload and Fan (x=681)
    hdr[0:60, 680:682] = (24.0, 24.0, 24.0)

    hdr_img = Image.fromarray(np.clip(hdr, 0, 255).astype(np.uint8)).resize(
        (W, sy(66)), Image.Resampling.LANCZOS
    ).convert("RGBA")

    img = Image.new("RGBA", (W, H), BG_MAIN + (255,))
    img.paste(hdr_img, (0, 0))

    # 2. 3 Fan cards: Model fan, Auxiliary fan, Case fan
    title_fnt = load_font(12, bold=True)
    cards = [
        ("Model fan", 42),
        ("Auxiliary fan", 104),
        ("Case fan", 166),
    ]
    for title, y0 in cards:
        y1 = y0 + 54
        draw_glow_box(img, (14, y0, 466, y1), radius=9, fill=(24, 24, 26), outline=LINE_AMBER, glow_alpha=20, width=1)
        draw_fan_glyph(img, (24, y0 + 10, 58, y0 + 44))
        d = ImageDraw.Draw(img)
        d.text((68, y0 + 9), title, fill=TEXT_LIGHT + (255,), font=title_fnt)

    # Bottom nav bar matching move.png
    d = ImageDraw.Draw(img)
    d.line((0, 230, W, 230), fill=LINE_AMBER + (255,), width=1)
    d.rectangle((0, 231, W, H), fill=BG_NAV + (255,))
    return img.convert("RGB")


def draw_nozzle_thermometer_icon(img: Image.Image, cx: int, top_y: int) -> None:
    """
    Draw the amber nozzle-with-thermometer outline icon (supersampled 4x)
    matching the stock SK1 Load/Unload reference.
    """
    ss = 4
    w, h = 60, 62
    hi = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(hi)
    mx = (w * ss) // 2

    def draw_shape(target: ImageDraw.ImageDraw, col: tuple[int, int, int, int], lw: int) -> None:
        # Outer hotend housing (rounded top corners) + flared collar + nozzle tip
        # Rounded top body
        target.rounded_rectangle(
            (mx - 15 * ss, 6 * ss, mx + 15 * ss, 39 * ss),
            radius=4 * ss,
            outline=col,
            width=lw,
        )
        # Cover bottom horizontal edge of rounded_rect where collar flares
        target.rectangle((mx - 14 * ss, 34 * ss, mx + 14 * ss, 40 * ss), fill=BG_WELL + (255,))
        # Flared collar + nozzle triangle
        collar = [
            (mx - 15 * ss, 35 * ss),
            (mx - 20 * ss, 35 * ss),
            (mx - 20 * ss, 42 * ss),
            (mx - 13 * ss, 42 * ss),
            (mx, 56 * ss),
            (mx + 13 * ss, 42 * ss),
            (mx + 20 * ss, 42 * ss),
            (mx + 20 * ss, 35 * ss),
            (mx + 15 * ss, 35 * ss),
        ]
        target.line(collar, fill=col, width=lw, joint="curve")

        # Inner thermometer stem + bulb
        stem_x0 = mx - 4 * ss
        stem_x1 = mx + 4 * ss
        target.rounded_rectangle(
            (stem_x0, 11 * ss, stem_x1, 35 * ss),
            radius=4 * ss,
            outline=col,
            width=lw,
        )
        # Bulb at bottom of thermometer
        br = 7 * ss
        by = 38 * ss
        target.ellipse((mx - br, by - br, mx + br, by + br), outline=col, fill=BG_WELL + (255,), width=lw)
        # Inner mercury core & stem
        target.ellipse((mx - 3 * ss, by - 3 * ss, mx + 3 * ss, by + 3 * ss), fill=col)
        target.rectangle((mx - 1 * ss, 19 * ss, mx + 1 * ss, by), fill=col)
        # Scale ticks on right side of thermometer stem
        for ty in (16, 21, 26):
            target.line((mx + 2 * ss, ty * ss, mx + 7 * ss, ty * ss), fill=col, width=max(2, lw - 1))

    # Glow pass
    glow = Image.new("RGBA", hi.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    draw_shape(gd, AMBER + (135,), 3 * ss)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=3 * ss))

    # Crisp pass
    hi = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(hi)
    draw_shape(d, AMBER_BRIGHT + (255,), 2 * ss)

    combined = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    combined.alpha_composite(glow)
    combined.alpha_composite(hi)
    icon_img = combined.resize((w, h), Image.Resampling.LANCZOS)
    img.alpha_composite(icon_img, (cx - w // 2, top_y))


def build_nozzle_thermometer_sprite() -> None:
    """Export standalone 60x62 amber nozzle-with-thermometer RGBA sprite."""
    w, h = 60, 62
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_nozzle_thermometer_icon(img, cx=w // 2, top_y=0)
    img.save(UI_DIR / "nozzle_therm.png")

    # Standalone 24x16 crisp arrow sprite for active Load/Unload temp row
    aw, ah = 24, 16
    arr_img = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arr_img)
    cy = ah // 2
    ad.rectangle((3, cy - 2, 14, cy + 2), fill=TEXT_LIGHT + (255,))
    ad.polygon([(13, cy - 5), (21, cy), (13, cy + 5)], fill=TEXT_LIGHT + (255,))
    arr_img.save(UI_DIR / "temp_arrow.png")


def build_load_bg(m0: np.ndarray) -> Image.Image:
    """Stock-styled Load/Unload page with Move/Temp header (Load/Unload active) + stepper + clean right card."""
    hdr = m0[0:66, 0:1024].copy().astype(np.float32)

    # Clean Wi-Fi + alert in top-right (x=936..1024) using tab 3 bg [37,37,37]
    hdr[0:62, 936:1024] = m0[0:62, 710:798]

    # Tab 1 (Move/Temp, x=0..341): switch active [23,23,23] -> inactive [37,37,37] + muted text
    t1 = hdr[0:63, 0:341]
    alpha1 = np.clip(np.max(t1 - 23.0, axis=2) / (230.0 - 23.0), 0.0, 1.0)
    bg_inact = np.array([37.0, 37.0, 37.0])
    fg_muted = np.array([145.0, 118.0, 96.0])
    hdr[0:60, 0:341] = bg_inact + alpha1[0:60, :, None] * (fg_muted - bg_inact)
    hdr[60:63, 0:341] = hdr[60:63, 710:711]

    # Tab 2 (Load/Unload, x=342..681): switch inactive [37,37,37] -> active [23,23,23] + bright text
    t2 = hdr[0:63, 342:681]
    alpha2 = np.clip(np.max(t2 - 37.0, axis=2) / (145.0 - 37.0), 0.0, 1.0)
    bg_act = np.array([23.0, 23.0, 23.0])
    fg_bright = np.array([243.0, 205.0, 166.0])
    hdr[0:60, 342:681] = bg_act + alpha2[0:60, :, None] * (fg_bright - bg_act)
    hdr[60:66, 342:681] = bg_act
    # Clean tab dividers
    hdr[0:60, 340:342] = (24.0, 24.0, 24.0)
    hdr[0:60, 680:682] = (24.0, 24.0, 24.0)

    hdr_img = Image.fromarray(np.clip(hdr, 0, 255).astype(np.uint8)).resize(
        (W, sy(66)), Image.Resampling.LANCZOS
    ).convert("RGBA")

    img = Image.new("RGBA", (W, H), BG_MAIN + (255,))
    img.paste(hdr_img, (0, 0))

    # Left stepper card (x: 12..162, y: 42..218)
    draw_glow_box(img, (12, 42, 162, 218), radius=9, fill=(24, 24, 26), outline=LINE_DARK, glow_alpha=18, width=1)
    d = ImageDraw.Draw(img)
    # Horizontal divider under mode title
    d.line((20, 70, 154, 70), fill=(115, 102, 84, 255), width=1)
    # Vertical stepper line connecting circles 1 -> 2 -> 3
    cx = 32
    ys = (94, 139, 184)
    d.line((cx, ys[0], cx, ys[2]), fill=(195, 182, 160, 255), width=2)
    num_fnt = load_font(10, bold=True)
    for idx, cy in enumerate(ys, start=1):
        r = 7
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(238, 226, 205, 255), outline=AMBER_DIM + (255,), width=1)
        d.text((cx, cy), str(idx), fill=(22, 22, 24, 255), font=num_fnt, anchor="mm")

    # Right main card (x: 170..468, y: 42..218) — clean container for idle selector & active view
    draw_glow_box(img, (170, 42, 468, 218), radius=9, fill=(24, 24, 26), outline=LINE_AMBER, glow_alpha=20, width=1)

    # Bottom nav bar matching move.png
    d = ImageDraw.Draw(img)
    d.line((0, 230, W, 230), fill=LINE_AMBER + (255,), width=1)
    d.rectangle((0, 231, W, H), fill=BG_NAV + (255,))
    return img.convert("RGB")


def build_load_action_sprites() -> None:
    """Load/Unload action button sprites + left/right temperature step arrow sprites."""
    w, h = 100, 38
    fnt = load_font(13, bold=True)

    configs = [
        ("load", "Load", AMBER, AMBER_BRIGHT),
        ("unload", "Unload", (218, 72, 62), (242, 118, 108)),
    ]
    for slug, label, glow_rgb, text_active_rgb in configs:
        # Inactive pill
        inact = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        idraw = ImageDraw.Draw(inact)
        idraw.rounded_rectangle((3, 3, w - 4, h - 4), radius=8, fill=(44, 44, 50, 255), outline=(74, 70, 66, 255), width=1)
        idraw.text((w // 2, h // 2), label, fill=TEXT_LIGHT + (255,), font=fnt, anchor="mm")
        inact.save(UI_DIR / f"{slug}_inactive.png")

        # Active pill with outer glow
        act = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.rounded_rectangle((2, 2, w - 3, h - 3), radius=9, fill=glow_rgb + (90,))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=3))
        act.alpha_composite(glow)
        ad = ImageDraw.Draw(act)
        ad.rounded_rectangle((3, 3, w - 4, h - 4), radius=8, fill=(28, 28, 34, 255), outline=glow_rgb + (255,), width=2)
        ad.text((w // 2, h // 2), label, fill=text_active_rgb + (255,), font=fnt, anchor="mm")
        act.save(UI_DIR / f"{slug}_active.png")

    # Left / Right nozzle temperature selector buttons (46x38) matching reference outline style
    aw, ah = 46, 38
    for slug, direction in (("temp_left_btn", -1), ("temp_right_btn", 1)):
        btn = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
        bd = ImageDraw.Draw(btn)
        bd.rounded_rectangle((2, 2, aw - 3, ah - 3), radius=8, fill=(30, 30, 34, 255), outline=(145, 134, 118, 255), width=1)
        cx, cy = aw // 2, ah // 2
        if direction < 0:
            tri = [(cx - 6, cy), (cx + 5, cy - 7), (cx + 5, cy + 7)]
        else:
            tri = [(cx + 6, cy), (cx - 5, cy - 7), (cx - 5, cy + 7)]
        bd.polygon(tri, fill=TEXT_LIGHT + (255,))
        btn.save(UI_DIR / f"{slug}.png")


def build_generic_stock_bg(page: str) -> Image.Image:
    img = make_stock_shell_bg()
    if page in ("zoffset", "calibrate", "network", "settings"):
        draw_glow_box(img, (14, 52, 466, 218), radius=10, fill=(20, 20, 22), outline=LINE_DARK, glow_alpha=20, width=1)
    return img.convert("RGB")


def make_alpha_from_bg(crop: np.ndarray, bg_rgb: tuple[int, int, int], lo: int = 8, hi: int = 38) -> Image.Image:
    """Convert dark-background crop into smooth RGBA sprite by distance from bg color."""
    diff = np.linalg.norm(crop.astype(np.float32) - np.array(bg_rgb, dtype=np.float32), axis=2)
    alpha = np.clip((diff - lo) / max(1, hi - lo), 0.0, 1.0)
    rgba = np.zeros((crop.shape[0], crop.shape[1], 4), dtype=np.uint8)
    rgba[:, :, :3] = crop
    rgba[:, :, 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def recolor_amber_glow(glyph_rgba: Image.Image) -> Image.Image:
    """Turn a muted bronze/brown icon glyph into bright glowing amber matching active stock icons."""
    arr = np.array(glyph_rgba).astype(np.float32)
    a = arr[:, :, 3:4] / 255.0
    # Crisp bright amber (255, 162, 24) matching nav_home_active / nav_move_active
    bright = np.zeros_like(arr)
    bright[:, :, 0] = 255
    bright[:, :, 1] = 162
    bright[:, :, 2] = 24
    bright[:, :, 3] = arr[:, :, 3]
    fg = Image.fromarray(bright.astype(np.uint8), "RGBA")

    # Add soft amber outer glow behind glyph
    glow_src = Image.new("RGBA", fg.size, (255, 145, 0, 0))
    glow_arr = np.array(glow_src)
    glow_arr[:, :, 3] = (a[:, :, 0] * 125).astype(np.uint8)
    glow = Image.fromarray(glow_arr, "RGBA").filter(ImageFilter.GaussianBlur(radius=3))
    out = Image.new("RGBA", fg.size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(fg)
    return out


def build_nav_sprites(h0: np.ndarray, m0: np.ndarray) -> None:
    """
    Crop the 5 nav icons (inactive & active) from the two reference prints,
    and compose active glowing rounded-amber-box states for files, settings, print.
    Target sprite size: 46x36 at 480x272 (cropped at 98x77 around cy=530 in 1024x572).
    """
    half_w, half_h = 49, 39  # 98x78 in 1024x572 -> 46x36 at 480x272
    cy = 530
    centers = {
        "home": 157,
        "move": 335,
        "files": 515,
        "settings": 691,
        "print": 844,
    }

    def crop_ref(arr: np.ndarray, cx: int) -> np.ndarray:
        return arr[cy - half_h : cy + half_h, cx - half_w : cx + half_w].copy()

    # Extract clean active glow frame template from home slot 0 by masking out inner house glyph
    home_act_hi = crop_ref(h0, centers["home"])
    frame_hi = home_act_hi.copy()
    # Inner icon sits inside margin [20..58, 28..70] in 98x78 crop; clear to [22, 20, 18]
    # Check outer ring vs inner glyph: frame border is around y=6..70, x=5..92
    frame_hi[20:58, 29:69] = (20, 20, 20)
    frame_rgba = make_alpha_from_bg(frame_hi, BG_NAV, lo=5, hi=26).resize((46, 36), Image.Resampling.LANCZOS)

    # Crop exact active states present in prints
    nav_home_active = make_alpha_from_bg(crop_ref(h0, centers["home"]), BG_NAV, lo=5, hi=26).resize(
        (46, 36), Image.Resampling.LANCZOS
    )
    nav_move_active = make_alpha_from_bg(crop_ref(m0, centers["move"]), (21, 21, 21), lo=5, hi=26).resize(
        (46, 36), Image.Resampling.LANCZOS
    )

    # Crop exact inactive states present in prints
    inactive_sources = {
        "home": m0,
        "move": h0,
        "files": h0,
        "settings": h0,
        "print": h0,
    }

    nav_home_active.save(UI_DIR / "nav_home_active.png")
    nav_move_active.save(UI_DIR / "nav_move_active.png")

    for name, src in inactive_sources.items():
        raw = crop_ref(src, centers[name])
        inactive_rgba = make_alpha_from_bg(raw, BG_NAV, lo=8, hi=32).resize((46, 36), Image.Resampling.LANCZOS)
        inactive_rgba.save(UI_DIR / f"nav_{name}_inactive.png")

        if name not in ("home", "move"):
            # Composite active frame + bright glowing glyph
            bright_glyph = recolor_amber_glow(inactive_rgba)
            composed = frame_rgba.copy()
            composed.alpha_composite(bright_glyph)
            composed.save(UI_DIR / f"nav_{name}_active.png")


def build_home_quick_sprites(h0: np.ndarray) -> None:
    """
    Crop Light & Fan recessed button boxes from h0 and synthesize complementary OFF/ON states.
    Light box in h0: x=6..156, y=410..476 -> 70x31 at 480x272
    Fan box in h0:   x=166..318, y=410..476 -> 71x31 at 480x272
    """
    light_crop = h0[410:476, 6:156].copy()
    fan_crop = h0[410:476, 166:318].copy()

    # Light ON = directly from h0 (bright glowing bulb in dark recessed box)
    light_on = Image.fromarray(light_crop).resize((70, 31), Image.Resampling.LANCZOS).convert("RGBA")
    light_on.save(UI_DIR / "light_on.png")

    # Light OFF = keep box border, dim the glowing bulb to muted warm-gray
    lo_arr = np.array(light_on).astype(np.float32)
    # Detect bright amber pixels inside inner icon area (x=15..55, y=4..27)
    inner = lo_arr[4:27, 15:55]
    bright_mask = (inner[:, :, 0] > 45)
    # Replace glowing yellow-orange with muted #6a6258 proportional to brightness
    lum = np.clip((inner[:, :, 0] - 31) / 224.0, 0.0, 1.0)
    inner[bright_mask, 0] = 31 + lum[bright_mask] * 78
    inner[bright_mask, 1] = 31 + lum[bright_mask] * 70
    inner[bright_mask, 2] = 31 + lum[bright_mask] * 60
    light_off = Image.fromarray(lo_arr.astype(np.uint8), "RGBA")
    light_off.save(UI_DIR / "light_off.png")

    # Fan in h0 is dim/idle amber ring. Let's make fan_off clearly muted and fan_on bright glowing amber!
    fan_base = Image.fromarray(fan_crop).resize((71, 31), Image.Resampling.LANCZOS).convert("RGBA")

    # Fan OFF: mute amber ring/blades uniformly to subtle #6a6258
    fo_arr = np.array(fan_base).astype(np.float32)
    f_inner = fo_arr[3:28, 12:59]
    f_mask = (f_inner[:, :, 0] > 35)
    flum = np.clip((f_inner[:, :, 0] - 31) / 180.0, 0.0, 1.0)
    f_inner[f_mask, 0] = 31 + flum[f_mask] * 76
    f_inner[f_mask, 1] = 31 + flum[f_mask] * 68
    f_inner[f_mask, 2] = 31 + flum[f_mask] * 58
    Image.fromarray(fo_arr.astype(np.uint8), "RGBA").save(UI_DIR / "fan_off.png")

    # Fan ON: brighten fan glyph + warm outer amber glow inside box matching light_on
    fan_on = fan_base.copy()
    fn_arr = np.array(fan_on).astype(np.float32)
    fn_in = fn_arr[3:28, 12:59]
    fn_lum = np.clip((fn_in[:, :, 0] - 31) / 160.0, 0.0, 1.0)
    mask = fn_in[:, :, 0] > 36
    fn_in[mask, 0] = np.clip(31 + fn_lum[mask] * 224, 0, 255)
    fn_in[mask, 1] = np.clip(31 + fn_lum[mask] * 145, 0, 255)
    fn_in[mask, 2] = np.clip(31 + fn_lum[mask] * 15, 0, 255)
    glow_layer = Image.new("RGBA", fan_on.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.ellipse((24, 5, 47, 26), fill=(255, 160, 20, 68))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=4))
    out_fan = Image.fromarray(fn_arr.astype(np.uint8), "RGBA")
    out_fan.alpha_composite(glow_layer)
    out_fan.save(UI_DIR / "fan_on.png")


def build_status_sprites(h0: np.ndarray, m0: np.ndarray) -> None:
    """Crop Wi-Fi and Alert icons from home reference and generate muted OFF variants."""
    wifi_crop = h0[12:56, 948:1004]
    wifi_on = make_alpha_from_bg(wifi_crop, (20, 20, 18), lo=18, hi=46).resize((26, 21), Image.Resampling.LANCZOS)
    wifi_on.save(UI_DIR / "wifi_on.png")

    # Muted disconnected wifi
    wo = np.array(wifi_on).astype(np.float32)
    wo[:, :, 0] = 105
    wo[:, :, 1] = 105
    wo[:, :, 2] = 110
    wo[:, :, 3] = (wo[:, :, 3] * 0.55).astype(np.float32)
    wifi_off = Image.fromarray(wo.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(wifi_off)
    d.line((4, 17, 22, 3), fill=(212, 91, 74, 220), width=2)
    wifi_off.save(UI_DIR / "wifi_off.png")

    alert_crop = h0[87:139, 946:1005]
    alert_on = make_alpha_from_bg(alert_crop, (20, 20, 18), lo=26, hi=55).resize((28, 24), Image.Resampling.LANCZOS)
    alert_on.save(UI_DIR / "alert_on.png")

    ao = np.array(alert_on).astype(np.float32)
    ao[:, :, 0] = 95
    ao[:, :, 1] = 95
    ao[:, :, 2] = 100
    ao[:, :, 3] = (ao[:, :, 3] * 0.4).astype(np.float32)
    Image.fromarray(ao.astype(np.uint8), "RGBA").save(UI_DIR / "alert_off.png")


def build_step_pill_sprites(m0: np.ndarray) -> None:
    """
    Crop inactive pill frame (from '1mm') and active glowing pill frame (from '10mm'),
    erase original text inside, and render crisp 0.1mm / 1mm / 10mm / 30mm states (72x34).
    """
    # Active box in m0: x=436..640, y=76..156 (204x80) -> center (538, 116)
    # Inactive 1mm box in m0: x=245..429, y=85..148 -> embed into same 204x80 canvas centered at (337, 116)
    hw, hh = 102, 40

    act_raw = m0[116 - hh : 116 + hh, 538 - hw : 538 + hw].copy()
    inact_raw = m0[116 - hh : 116 + hh, 337 - hw : 337 + hw].copy()

    # Clean inner text inside both pills using sampled dark pill interior [29, 29, 29]
    act_inner_bg = tuple(int(v) for v in act_raw[40, 26])
    inact_inner_bg = tuple(int(v) for v in inact_raw[40, 26])
    act_raw[21:59, 44:160] = act_inner_bg
    inact_raw[21:59, 44:160] = inact_inner_bg

    pw, ph = 70, 34
    act_frame = make_alpha_from_bg(act_raw, BG_MAIN, lo=4, hi=22).resize((pw, ph), Image.Resampling.LANCZOS)
    inact_frame = make_alpha_from_bg(inact_raw, BG_MAIN, lo=4, hi=22).resize((pw, ph), Image.Resampling.LANCZOS)

    act_frame.save(UI_DIR / "pill_active.png")
    inact_frame.save(UI_DIR / "pill_inactive.png")

    fnt = load_font(11, bold=False)
    steps = [
        ("01", "0.1mm"),
        ("1", "1mm"),
        ("10", "10mm"),
        ("30", "30mm"),
    ]
    for slug, label in steps:
        for state, frame, color in (
            ("inactive", inact_frame, (224, 206, 172, 235)),
            ("active", act_frame, (248, 232, 198, 255)),
        ):
            im = frame.copy()
            d = ImageDraw.Draw(im)
            d.text((pw // 2, ph // 2), label, fill=color, font=fnt, anchor="mm")
            im.save(UI_DIR / f"step_{slug}_{state}.png")


def main() -> None:
    if not REF_HOME.exists() or not REF_MOVE.exists():
        raise FileNotFoundError("Reference screenshots not found.")

    BG_DIR.mkdir(parents=True, exist_ok=True)
    UI_DIR.mkdir(parents=True, exist_ok=True)
    HMI_IMG_DIR.mkdir(parents=True, exist_ok=True)

    h0 = np.array(Image.open(REF_HOME).convert("RGB"))
    m0 = np.array(Image.open(REF_MOVE).convert("RGB"))

    # 1. Clean 480x272 backgrounds
    build_home_bg(h0).save(BG_DIR / "home.png")
    build_move_bg(m0).save(BG_DIR / "move.png")
    build_print_bg().save(BG_DIR / "print.png")
    build_files_bg().save(BG_DIR / "files.png")
    build_fans_bg(m0).save(BG_DIR / "fans.png")
    build_load_bg(m0).save(BG_DIR / "load.png")
    for p in ("zoffset", "calibrate", "network", "settings"):
        build_generic_stock_bg(p).save(BG_DIR / f"{p}.png")

    # 2. Cropped & synthesized UI state sprites
    build_nav_sprites(h0, m0)
    build_home_quick_sprites(h0)
    build_status_sprites(h0, m0)
    build_step_pill_sprites(m0)
    build_print_action_sprites()
    build_nozzle_thermometer_sprite()
    build_load_action_sprites()

    # 3. Sync backgrounds and UI sprites into hmi/images/
    for p in BG_DIR.glob("*.png"):
        shutil.copy2(p, HMI_IMG_DIR / p.name)
    for p in UI_DIR.glob("*.png"):
        shutil.copy2(p, HMI_IMG_DIR / p.name)

    print(f"Generated backgrounds in {BG_DIR}: {len(list(BG_DIR.glob('*.png')))}")
    print(f"Generated UI sprites in {UI_DIR}: {len(list(UI_DIR.glob('*.png')))}")


if __name__ == "__main__":
    main()
