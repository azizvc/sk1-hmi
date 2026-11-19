"""Ícones de título das páginas print e files (22×22, fundo transparente).

Não usar print.png / files.png em hmi/images — esses nomes são os backgrounds 480×272.

Uso:
    bridge\\.venv\\Scripts\\python.exe tools\\gen_title_icons.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from generate_assets import icon_files, icon_print  # noqa: E402

TITLE_SIZE = 22
SRC_SIZE = 48

OUT_DIRS = (
    ROOT / "assets" / "ui",
    ROOT / "hmi" / "images",
)


def _with_glow(src: Image.Image) -> Image.Image:
    """Leve brilho âmbar, como .title no preview (text-shadow)."""
    glow = Image.new("RGBA", src.size, (0, 0, 0, 0))
    glow.paste(src, (0, 0), src)
    glow = glow.filter(ImageFilter.GaussianBlur(1.2))
    # escurece o glow para não lavar o traço
    glow_bytes = glow.split()
    if len(glow_bytes) == 4:
        r, g, b, a = glow_bytes
        a = a.point(lambda x: int(x * 0.45))
        glow = Image.merge("RGBA", (r, g, b, a))
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    out = Image.alpha_composite(out, glow)
    out = Image.alpha_composite(out, src)
    return out


def title_icon(builder, size: int = TITLE_SIZE) -> Image.Image:
    base = builder(size=SRC_SIZE)
    scaled = base.resize((size, size), Image.Resampling.LANCZOS)
    return _with_glow(scaled)


def main() -> None:
    icons = {
        "title_print.png": icon_print,
        "title_files.png": icon_files,
    }
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    for name, builder in icons.items():
        img = title_icon(builder)
        for d in OUT_DIRS:
            path = d / name
            img.save(path, optimize=True)
            print(f"wrote {path} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()