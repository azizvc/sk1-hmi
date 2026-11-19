"""Gera trilho cheio (sem bolinha) e bolinha do slider da página fans.

Uso:
    bridge\\.venv\\Scripts\\python.exe tools\\gen_slider_assets.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT_DIRS = (ROOT / "assets" / "ui", ROOT / "hmi" / "images")

# Largura do h_part (388); altura da imagem 28px com barra 8px centralizada.
TRACK_W, TRACK_H = 388, 28
BAR_H = 8
THUMB = 16

# design-tokens + hmi/preview/styles.css
COL_BG = (20, 20, 22)  # #141416
COL_BORDER = (60, 52, 42)  # #3c342a
COL_FILL = (255, 153, 0)  # #ff9900
COL_FILL_HI = (255, 179, 56)
COL_THUMB = (255, 179, 56)  # #ffb338
COL_THUMB_RING = (26, 26, 28)  # #1a1a1c


def _rounded_bar(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], r: int, fill) -> None:
    draw.rounded_rectangle(xy, radius=r, fill=fill)


def track_full() -> Image.Image:
    """Trilho 100% preenchido, sem bolinha (para pic de progresso / referência)."""
    im = Image.new("RGBA", (TRACK_W, TRACK_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y0 = (TRACK_H - BAR_H) // 2
    y1 = y0 + BAR_H
    outer = (0, y0 - 1, TRACK_W - 1, y1)
    _rounded_bar(d, outer, BAR_H // 2 + 1, COL_BORDER)
    inner = (1, y0, TRACK_W - 2, y1 - 1)
    _rounded_bar(d, inner, BAR_H // 2, COL_BG)
    # preenchimento cheio
    fill_box = (2, y0 + 1, TRACK_W - 3, y1 - 2)
    _rounded_bar(d, fill_box, max(1, BAR_H // 2 - 1), COL_FILL)
    # leve brilho no topo
    hi = Image.new("RGBA", (TRACK_W, TRACK_H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    _rounded_bar(hd, (2, y0 + 1, TRACK_W - 3, y0 + BAR_H // 2), max(1, BAR_H // 4), COL_FILL_HI + (90,))
    im = Image.alpha_composite(im, hi)
    return im


def track_empty() -> Image.Image:
    """Trilho vazio (só canal), sem bolinha — útil como pic de fundo no USART."""
    im = Image.new("RGBA", (TRACK_W, TRACK_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y0 = (TRACK_H - BAR_H) // 2
    y1 = y0 + BAR_H
    _rounded_bar(d, (0, y0 - 1, TRACK_W - 1, y1), BAR_H // 2 + 1, COL_BORDER)
    _rounded_bar(d, (1, y0, TRACK_W - 2, y1 - 1), BAR_H // 2, COL_BG)
    return im


def thumb() -> Image.Image:
    """Bolinha do slider, fundo transparente."""
    pad = 6
    size = THUMB + pad * 2
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = size // 2, size // 2
    # glow
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=(255, 153, 0, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(2))
    im = Image.alpha_composite(glow, im)
    d = ImageDraw.Draw(im)
    r = THUMB // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=COL_THUMB, outline=COL_THUMB_RING, width=2)
    return im


def main() -> None:
    assets = {
        "slider_track_full.png": track_full(),
        "slider_track_empty.png": track_empty(),
        "slider_thumb.png": thumb(),
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