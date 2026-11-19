from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .config import load_config
from .runtime import run_forever


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="sk1-hmi")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[2] / "packaging" / "config.example.toml"),
        help="Path to config.toml",
    )
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    level = getattr(logging, cfg.log.level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        asyncio.run(run_forever(cfg))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
