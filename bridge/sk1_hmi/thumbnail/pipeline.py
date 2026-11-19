from __future__ import annotations

import io
import logging
from pathlib import Path

from PIL import Image

log = logging.getLogger(__name__)


def extract_png_from_gcode(data: bytes) -> bytes | None:
    """Find first PNG embedded as base64 thumbnail in gcode comments if raw file given."""
    text = data.decode("utf-8", errors="ignore")
    marker = "; thumbnail begin"
    if marker not in text and "thumbnail_image" not in text:
        # maybe already an image
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return data
        if data[:2] == b"\xff\xd8":
            return data
        return None
    # Moonraker usually serves PNG/JPG directly via thumbnail relative_path
    return None


def resize_for_hmi(image_bytes: bytes, size: tuple[int, int] = (160, 160)) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(size, Image.Resampling.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def cache_path(cache_dir: Path, key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
    return cache_dir / f"{safe}.png"
