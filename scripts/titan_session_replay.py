#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from aoa_sdk.titans.session_replay import cli

    return cli()


if __name__ == "__main__":
    raise SystemExit(main())
