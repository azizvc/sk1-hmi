#!/usr/bin/env python3
"""Generate 480x272 page backgrounds and amber glyph icons for the HMI project."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG_DIR = ROOT / "assets" / "backgrounds"
ICON_DIR = ROOT / "assets" / "icons"

W, H = 480, 272
NAV_Y = 228
HDR_H = 32

# Deeper charcoal / near-black (stock SK1)
BG = (18, 18, 20)
ELEV = (28, 28, 32)
WELL = (24, 24, 28)
ACCENT = (255, 153, 0)
ACCENT_DIM = (180, 110, 20)
TEXT = (242, 240, 235)
MUTED = (120, 120, 126)
LINE = (48, 48, 54)
DANGER = (212, 91, 74)
HOTEND = (255, 153, 0)
BED = (255, 153, 0)

PAGES = [
    ("home", "SK1"),
    ("print", "Print"),
    ("move", "Move"),
    ("files", "Files"),
    ("fans", "Fans"),
    ("zoffset", "Z-Offset"),
    ("calibrate", "Calibrate"),
    ("network", "Network"),
    ("settings", "Settings"),
]


def font(size: int):
    for name in (
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        p = Path(name)
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def paste_tt_logo(img: Image.Image, xy=(8, 4), size=28) -> None:
    logo_path = ICON_DIR / "tt-logo.png"
    if not logo_path.exists():
        return
    logo = Image.open(logo_path).convert("RGBA")
    logo = logo.resize((size, size), Image.Resampling.LANCZOS)
    px = logo.load()
    for y in range(logo.height):
        for x in range(logo.width):
            r, g, b, a = px[x, y]
            if r < 40 and g < 40 and b < 40:
                px[x, y] = (0, 0, 0, 0)
    img.paste(logo, xy, logo)


def draw_glow_rect(
    base: Image.Image,
    box: tuple[int, int, int, int],
    radius: int = 10,
    glow: tuple[int, int, int, int] = (255, 153, 0, 70),
    fill: tuple[int, int, int] = WELL,
    outline: tuple[int, int, int] = ACCENT,
    width: int = 2,
) -> None:
    """Soft amber outer glow + inset well (baked into PNG)."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    pad = 6
    ld.rounded_rectangle(
        (x0 - pad, y0 - pad, x1 + pad, y1 + pad),
        radius=radius + 2,
        fill=glow,
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius=4))
    base.alpha_composite(layer)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    # subtle neumorphic inset edge
    d.rounded_rectangle(
        (x0 + 1, y0 + 1, x1 - 1, y1 - 1),
        radius=max(1, radius - 1),
        outline=(12, 12, 14),
        width=1,
    )


def draw_wifi(d: ImageDraw.ImageDraw, x: int, y: int, color=ACCENT) -> None:
    d.arc((x, y + 8, x + 16, y + 24), 220, 320, fill=color, width=2)
    d.arc((x + 3, y + 11, x + 13, y + 21), 220, 320, fill=color, width=2)
    d.ellipse((x + 6, y + 16, x + 10, y + 20), fill=color)


def draw_alert(d: ImageDraw.ImageDraw, x: int, y: int, color=ACCENT) -> None:
    d.ellipse((x, y, x + 16, y + 16), outline=color, width=2)
    d.line((x + 8, y + 4, x + 8, y + 10), fill=color, width=2)
    d.ellipse((x + 7, y + 12, x + 9, y + 14), fill=color)


def draw_temp_graph(img: Image.Image) -> None:
    """Right-side stock-like temperature graph panel with wavy curves."""
    # panel
    x0, y0, x1, y1 = 128, 40, 468, 214
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((x0, y0, x1, y1), radius=8, fill=(22, 22, 26, 255), outline=LINE + (255,))
    # grid
    for i in range(1, 6):
        gy = y0 + int((y1 - y0) * i / 6)
        ld.line((x0 + 28, gy, x1 - 8, gy), fill=(40, 40, 46, 180), width=1)
    for i in range(1, 8):
        gx = x0 + 28 + int((x1 - x0 - 36) * i / 8)
        ld.line((gx, y0 + 8, gx, y1 - 8), fill=(36, 36, 42, 120), width=1)
    img.alpha_composite(layer)

    d = ImageDraw.Draw(img)
    # Y labels
    f = font(9)
    for label, frac in (("300", 0.08), ("200", 0.28), ("100", 0.52), ("0", 0.78), ("-15", 0.92)):
        yy = y0 + int((y1 - y0) * frac)
        d.text((x0 + 4, yy - 5), label, fill=MUTED, font=f)

    def curve(amp: float, phase: float, color: tuple[int, int, int], width: int = 2):
        pts = []
        left, right = x0 + 30, x1 - 10
        mid = (y0 + y1) // 2 + 10
        for i in range(left, right + 1, 2):
            t = (i - left) / max(1, right - left)
            yy = mid - int(math.sin(t * math.pi * 2.2 + phase) * amp * (0.55 + 0.45 * math.sin(t * math.pi)))
            # gentle trend down then up
            yy += int(18 * math.sin(t * math.pi + 0.3))
            pts.append((i, yy))
        if len(pts) > 1:
            d.line(pts, fill=color, width=width)

    curve(38, 0.2, ACCENT, 2)
    curve(28, 1.4, ACCENT_DIM, 2)

    draw_wifi(d, 428, 48)
    draw_alert(d, 448, 48)


def make_home_bg() -> Image.Image:
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    # header
    d.rectangle((0, 0, W, HDR_H), fill=ELEV)
    d.line((0, HDR_H, W, HDR_H), fill=ACCENT, width=2)
    paste_tt_logo(img, (6, 2), 28)
    d.text((38, 5), "SK1", fill=ACCENT, font=font(18))
    # nav bar
    d.rectangle((0, NAV_Y, W, H), fill=ELEV)
    d.line((0, NAV_Y, W, NAV_Y), fill=LINE, width=1)
    # left divider under logo area
    d.line((118, HDR_H + 4, 118, NAV_Y - 4), fill=LINE, width=1)
    # icon well placeholders (comps overlay icons/temps)
    draw_glow_rect(img, (22, 72, 70, 120), radius=10)
    draw_glow_rect(img, (82, 72, 130, 120), radius=10)
    # light / fan wells
    draw_glow_rect(img, (22, 168, 70, 212), radius=8, glow=(255, 153, 0, 55))
    draw_glow_rect(img, (82, 168, 130, 212), radius=8, glow=(255, 153, 0, 35), outline=ACCENT_DIM)
    draw_temp_graph(img)
    return img.convert("RGB")


def make_move_bg() -> Image.Image:
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, HDR_H), fill=ELEV)
    d.line((0, HDR_H, W, HDR_H), fill=ACCENT, width=2)
    # top tabs (stock Move/Temp | Load/Unload | Fan)
    d.text((12, 7), "Move/Temp", fill=ACCENT, font=font(13))
    d.text((110, 7), "Load/Unload", fill=MUTED, font=font(13))
    d.text((220, 7), "Fan", fill=MUTED, font=font(13))
    draw_wifi(d, 428, 8)
    draw_alert(d, 448, 8)
    d.rectangle((0, NAV_Y, W, H), fill=ELEV)
    d.line((0, NAV_Y, W, NAV_Y), fill=LINE, width=1)
    # left status rail frame
    rail = (8, 40, 100, 214)
    d.rounded_rectangle(rail, radius=8, outline=LINE, width=1, fill=(22, 22, 26))
    d.line((14, 96, 94, 96), fill=ACCENT_DIM, width=1)
    d.line((14, 154, 94, 154), fill=ACCENT_DIM, width=1)
    # three glowing wells
    draw_glow_rect(img, (16, 48, 56, 88), radius=8)
    draw_glow_rect(img, (16, 106, 56, 146), radius=8)
    draw_glow_rect(img, (16, 164, 56, 204), radius=8)
    return img.convert("RGB")


def make_generic_bg(page: str = "") -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, HDR_H), fill=ELEV)
    d.line((0, HDR_H, W, HDR_H), fill=ACCENT, width=2)
    d.rectangle((0, NAV_Y, W, H), fill=ELEV)
    d.line((0, NAV_Y, W, NAV_Y), fill=LINE, width=1)
    if page == "print":
        # thumb well + progress track cue
        d.rounded_rectangle((360, 44, 464, 148), radius=8, outline=LINE, width=1, fill=WELL)
        d.rounded_rectangle((16, 52, 330, 66), radius=4, outline=LINE, width=1, fill=(22, 22, 26))
    return img


def make_bg(title: str, brand: bool = False, page: str = "") -> Image.Image:
    if brand or page == "home":
        return make_home_bg()
    if page == "move":
        return make_move_bg()
    return make_generic_bg(page)


def _blank(size=48) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def icon_home(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.polygon([(24, 8), (40, 22), (34, 22), (34, 40), (14, 40), (14, 22), (8, 22)], outline=color, width=2)
    d.rectangle((20, 28, 28, 40), outline=color, width=2)
    return img


def icon_print(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.rectangle((18, 6, 30, 14), outline=color, width=2)
    d.polygon([(18, 14), (30, 14), (26, 22), (22, 22)], outline=color, width=2)
    d.line((24, 22, 24, 28), fill=color, width=2)
    d.rounded_rectangle((10, 30, 38, 40), radius=2, outline=color, width=2)
    d.line((14, 35, 34, 35), fill=color, width=1)
    return img


def icon_move(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.polygon([(24, 6), (30, 14), (18, 14)], fill=color)
    d.polygon([(24, 42), (30, 34), (18, 34)], fill=color)
    d.polygon([(6, 24), (14, 18), (14, 30)], fill=color)
    d.polygon([(42, 24), (34, 18), (34, 30)], fill=color)
    d.ellipse((19, 19, 29, 29), outline=color, width=2)
    return img


def icon_files(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.rounded_rectangle((10, 16, 38, 40), radius=3, outline=color, width=2)
    d.polygon([(10, 20), (10, 14), (22, 14), (26, 18), (38, 18), (38, 22)], outline=color, width=2)
    return img


def icon_more(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    cx, cy, r = 24, 24, 10
    for i in range(8):
        a = i * math.pi / 4
        x0 = cx + int(math.cos(a) * (r + 6))
        y0 = cy + int(math.sin(a) * (r + 6))
        x1 = cx + int(math.cos(a) * (r + 1))
        y1 = cy + int(math.sin(a) * (r + 1))
        d.line((x0, y0, x1, y1), fill=color, width=3)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=2)
    d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=color)
    return img


def icon_light(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.ellipse((14, 8, 34, 28), outline=color, width=2)
    d.rectangle((19, 28, 29, 34), outline=color, width=2)
    d.line((20, 36, 28, 36), fill=color, width=2)
    d.line((21, 39, 27, 39), fill=color, width=2)
    d.line((24, 2, 24, 6), fill=color, width=2)
    d.line((8, 18, 12, 18), fill=color, width=2)
    d.line((36, 18, 40, 18), fill=color, width=2)
    d.line((12, 8, 15, 11), fill=color, width=2)
    d.line((36, 8, 33, 11), fill=color, width=2)
    return img


def icon_fan(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    cx, cy = 24, 24
    d.ellipse((8, 8, 40, 40), outline=color, width=2)
    for i in range(3):
        a0 = i * (2 * math.pi / 3) - 0.4
        a1 = a0 + 1.2
        pts = [(cx, cy)]
        for j in range(8):
            t = a0 + (a1 - a0) * j / 7
            r = 6 + 8 * math.sin((j / 7) * math.pi)
            pts.append((cx + int(math.cos(t) * r), cy + int(math.sin(t) * r)))
        d.polygon(pts, fill=color)
    d.ellipse((20, 20, 28, 28), fill=BG + (255,), outline=color, width=1)
    return img


def icon_nozzle(color=HOTEND, size=48) -> Image.Image:
    img, d = _blank(size)
    d.polygon([(16, 8), (32, 8), (32, 22), (26, 36), (22, 36), (16, 22)], outline=color, width=2)
    d.line((24, 12, 24, 28), fill=color, width=2)
    d.ellipse((20, 26, 28, 34), outline=color, width=2)
    d.ellipse((22, 28, 26, 32), fill=color)
    return img


def icon_bed(color=BED, size=48) -> Image.Image:
    img, d = _blank(size)
    d.rounded_rectangle((8, 30, 40, 40), radius=2, outline=color, width=2)
    d.line((10, 34, 38, 34), fill=color, width=1)
    for x in (16, 24, 32):
        d.line([(x, 26), (x - 3, 20), (x + 3, 14), (x, 8)], fill=color, width=2)
    return img


def icon_pause(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.rectangle((14, 12, 20, 36), fill=color)
    d.rectangle((28, 12, 34, 36), fill=color)
    return img


def icon_cancel(color=DANGER, size=48) -> Image.Image:
    img, d = _blank(size)
    d.line((14, 14, 34, 34), fill=color, width=3)
    d.line((34, 14, 14, 34), fill=color, width=3)
    return img


def icon_stop(color=DANGER, size=48) -> Image.Image:
    img, d = _blank(size)
    d.rounded_rectangle((12, 12, 36, 36), radius=4, fill=color)
    return img


def icon_arrow_up(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.polygon([(24, 10), (36, 26), (28, 26), (28, 38), (20, 38), (20, 26), (12, 26)], fill=color)
    return img


def icon_arrow_down(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.polygon([(24, 38), (36, 22), (28, 22), (28, 10), (20, 10), (20, 22), (12, 22)], fill=color)
    return img


def icon_arrow_left(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.polygon([(10, 24), (26, 12), (26, 20), (38, 20), (38, 28), (26, 28), (26, 36)], fill=color)
    return img


def icon_arrow_right(color=ACCENT, size=48) -> Image.Image:
    img, d = _blank(size)
    d.polygon([(38, 24), (22, 12), (22, 20), (10, 20), (10, 28), (22, 28), (22, 36)], fill=color)
    return img


ICON_BUILDERS = {
    "home": icon_home,
    "print": icon_print,
    "move": icon_move,
    "files": icon_files,
    "more": icon_more,
    "light": icon_light,
    "fan": icon_fan,
    "nozzle": icon_nozzle,
    "bed": icon_bed,
    "pause": icon_pause,
    "cancel": icon_cancel,
    "stop": icon_stop,
    "arrow_up": icon_arrow_up,
    "arrow_down": icon_arrow_down,
    "arrow_left": icon_arrow_left,
    "arrow_right": icon_arrow_right,
}


def main() -> None:
    BG_DIR.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    for key, title in PAGES:
        make_bg(title, brand=(key == "home"), page=key).save(BG_DIR / f"{key}.png")
    for name, builder in ICON_BUILDERS.items():
        builder().save(ICON_DIR / f"{name}.png")
    img_dir = ROOT / "hmi" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for p in BG_DIR.glob("*.png"):
        Image.open(p).save(img_dir / p.name)
    for p in ICON_DIR.glob("*.png"):
        if p.name == "tt-logo.png":
            continue
        Image.open(p).convert("RGBA").save(img_dir / p.name)
    print(f"wrote {W}x{H} backgrounds to {BG_DIR}")
    print(f"wrote {len(ICON_BUILDERS)} icons to {ICON_DIR}")


if __name__ == "__main__":
    main()
