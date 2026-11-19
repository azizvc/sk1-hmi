"""Botões − / + do Z-offset na tela print (50×34, fundo transparente).

Alinhado a b_z_m / b_z_p no .HMI (x/y/w/h) e ao card Z-OFF do preview.

Uso:
    bridge\\.venv\\Scripts\\python.exe tools\\gen_z_step_btns.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]

OUT_DIRS = (ROOT / "assets" / "ui", ROOT / "hmi" / "images")

AMBER = (255, 149, 0)
AMBER_BRIGHT = (255, 200, 120)

W, H = 50, 34
OUTLINE = (122, 84, 32)  # #7a5420
FILL = (28, 28, 32)
GLYPH = (255, 179, 71)  # #ffb347


def _base() -> Image.Image:
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((1, 1, W - 2, H - 2), radius=8, fill=AMBER + (55,))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=2))
    base.alpha_composite(glow)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=8, fill=FILL + (255,), outline=OUTLINE + (255,), width=1)
    return base


def minus_btn() -> Image.Image:
    img = _base()
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    d.rounded_rectangle((cx - 9, cy - 2, cx + 9, cy + 2), radius=2, fill=GLYPH + (255,))
    return img


def plus_btn() -> Image.Image:
    img = _base()
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    d.rounded_rectangle((cx - 9, cy - 2, cx + 9, cy + 2), radius=2, fill=GLYPH + (255,))
    d.rounded_rectangle((cx - 2, cy - 9, cx + 2, cy + 9), radius=2, fill=GLYPH + (255,))
    return img


def minus_pressed() -> Image.Image:
    img = minus_btn()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=8, fill=(18, 18, 20, 80))
    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=8, outline=AMBER_BRIGHT + (255,), width=2)
    img = Image.alpha_composite(img, overlay)
    return img


def plus_pressed() -> Image.Image:
    img = plus_btn()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=8, fill=(18, 18, 20, 80))
    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=8, outline=AMBER_BRIGHT + (255,), width=2)
    img = Image.alpha_composite(img, overlay)
    return img


def main() -> None:
    assets = {
        "z_step_minus_btn.png": minus_btn(),
        "z_step_plus_btn.png": plus_btn(),
        "z_step_minus_pressed.png": minus_pressed(),
        "z_step_plus_pressed.png": plus_pressed(),
    }
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    for name, img in assets.items():
        for folder in OUT_DIRS:
            path = folder / name
            img.save(path, optimize=True)
            print(f"wrote {path} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()