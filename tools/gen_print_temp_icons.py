"""Ícones de hotend e mesa na tela print (18×18, âmbar, fundo transparente).

Usar em Picture ao lado de t_hotend / t_bed (não confundir com nozzle.png 48×48).

Uso:
    bridge\\.venv\\Scripts\\python.exe tools\\gen_print_temp_icons.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from generate_assets import icon_bed, icon_nozzle  # noqa: E402

PRINT_TEMP_SIZE = 18
SRC_SIZE = 48

OUT_DIRS = (
    ROOT / "assets" / "ui",
    ROOT / "hmi" / "images",
)


def _with_glow(src: Image.Image) -> Image.Image:
    glow = Image.new("RGBA", src.size, (0, 0, 0, 0))
    glow.paste(src, (0, 0), src)
    glow = glow.filter(ImageFilter.GaussianBlur(1.0))
    r, g, b, a = glow.split()
    a = a.point(lambda x: int(x * 0.4))
    glow = Image.merge("RGBA", (r, g, b, a))
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    out = Image.alpha_composite(out, glow)
    out = Image.alpha_composite(out, src)
    return out


def print_temp_icon(builder) -> Image.Image:
    base = builder(size=SRC_SIZE)
    scaled = base.resize((PRINT_TEMP_SIZE, PRINT_TEMP_SIZE), Image.Resampling.LANCZOS)
    return _with_glow(scaled)


def main() -> None:
    icons = {
        "print_temp_nozzle.png": icon_nozzle,
        "print_temp_bed.png": icon_bed,
    }
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    for name, builder in icons.items():
        img = print_temp_icon(builder)
        for d in OUT_DIRS:
            path = d / name
            img.save(path, optimize=True)
            print(f"wrote {path} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()