#!/usr/bin/env python3
"""Boot the bridge in dry-run for a few seconds without Moonraker/serial."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge"))

from sk1_hmi.app.state import AppState
from sk1_hmi.ui.render import render_full


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    state = AppState()
    state.temps.hotend = 210
    state.temps.bed = 60
    cmds = render_full(state)
    print(f"dry-run render produced {len(cmds)} HMI commands:")
    for c in cmds[:12]:
        print(" ", c)
    print("ok")


if __name__ == "__main__":
    asyncio.run(main())
