"""Botões Up / Down / Print na tela files (alinhados ao .HMI).

Tamanhos: 62×24 (up/down), 132×28 (print). Fundo transparente fora do chrome.

Uso:
    bridge\\.venv\\Scripts\\python.exe tools\\gen_files_btns.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from generate_assets import font, icon_print  # noqa: E402

OUT_DIRS = (ROOT / "assets" / "ui", ROOT / "hmi" / "images")

AMBER = (255, 153, 0)
AMBER_BRIGHT = (255, 200, 120)
OUTLINE_SEC = (110, 74, 26)  # #6e4a1a
OUTLINE_PRI = (255, 153, 0)
FILL = (28, 28, 32)
GLYPH = (243, 200, 130)  # #f3c882
TEXT_PRI = (255, 153, 0)

UP_W, UP_H = 62, 24
PRINT_W, PRINT_H = 132, 28


def _chrome(w: int, h: int, *, primary: bool = False) -> Image.Image:
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow_c = AMBER if primary else OUTLINE_SEC
    glow_a = 70 if primary else 40
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    radius = min(10, h // 2)
    gd.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=glow_c + (glow_a,))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=2))
    base.alpha_composite(glow)
    outline = OUTLINE_PRI if primary else OUTLINE_SEC
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(
        (1, 1, w - 2, h - 2),
        radius=radius - 1,
        fill=FILL + (255,),
        outline=outline + (255,),
        width=1,
    )
    # Inset highlight (preview linear-gradient)
    hi = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hd.rounded_rectangle((2, 2, w - 3, h // 2), radius=radius - 2, fill=(255, 255, 255, 18))
    base = Image.alpha_composite(base, hi)
    return base


def _pressed(img: Image.Image) -> Image.Image:
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    radius = min(10, h // 2) - 1
    d.rounded_rectangle((1, 1, w - 2, h - 2), radius=radius, fill=(18, 18, 20, 90))
    d.rounded_rectangle((1, 1, w - 2, h - 2), radius=radius, outline=AMBER_BRIGHT + (255,), width=2)
    return Image.alpha_composite(img, overlay)


def up_btn() -> Image.Image:
    img = _chrome(UP_W, UP_H)
    d = ImageDraw.Draw(img)
    cx, cy = UP_W // 2, UP_H // 2
    d.polygon([(cx, cy - 7), (cx + 7, cy + 5), (cx - 7, cy + 5)], fill=GLYPH + (255,))
    return img


def down_btn() -> Image.Image:
    img = _chrome(UP_W, UP_H)
    d = ImageDraw.Draw(img)
    cx, cy = UP_W // 2, UP_H // 2
    d.polygon([(cx, cy + 7), (cx + 7, cy - 5), (cx - 7, cy - 5)], fill=GLYPH + (255,))
    return img


def print_btn() -> Image.Image:
    img = _chrome(PRINT_W, PRINT_H, primary=True)
    glyph = icon_print(color=TEXT_PRI, size=48).resize((18, 18), Image.Resampling.LANCZOS)
    img.alpha_composite(glyph, (10, (PRINT_H - 18) // 2))
    d = ImageDraw.Draw(img)
    fnt = font(12)
    label = "Print"
    tw = d.textlength(label, font=fnt)
    tx = max(34, (PRINT_W - tw) // 2)
    ty = (PRINT_H - 12) // 2 - 1
    d.text((tx, ty), label, fill=TEXT_PRI + (255,), font=fnt)
    return img


def main() -> None:
    assets = {
        "files_up_btn.png": up_btn,
        "files_down_btn.png": down_btn,
        "files_print_btn.png": print_btn,
    }
    pressed = {
        "files_up_pressed.png": lambda: _pressed(up_btn()),
        "files_down_pressed.png": lambda: _pressed(down_btn()),
        "files_print_pressed.png": lambda: _pressed(print_btn()),
    }
    all_assets = {**assets, **pressed}
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    for name, builder in all_assets.items():
        img = builder()
        for folder in OUT_DIRS:
            path = folder / name
            img.save(path, optimize=True)
            print(f"wrote {path} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()