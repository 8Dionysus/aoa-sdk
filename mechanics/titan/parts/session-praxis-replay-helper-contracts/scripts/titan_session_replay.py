#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "src" / "aoa_sdk").is_dir():
            return parent
    raise RuntimeError("cannot locate aoa-sdk repo root from titan_session_replay.py")


ROOT = _repo_root()
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from aoa_sdk.titans.session_replay import cli

    return cli()


if __name__ == "__main__":
    raise SystemExit(main())
