#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def main() -> int:
    from aoa_sdk.titans.memory_loom import main as memory_loom_main

    return memory_loom_main()

if __name__ == "__main__":
    raise SystemExit(main())
