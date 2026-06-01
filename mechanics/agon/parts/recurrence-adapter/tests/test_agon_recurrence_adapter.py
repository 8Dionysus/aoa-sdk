from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PART_ROOT = Path(__file__).resolve().parents[1]


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "aoa_sdk").is_dir():
            return candidate
    raise RuntimeError(f"could not find aoa-sdk repo root from {start}")


def test_agon_recurrence_adapter_validates():
    result = subprocess.run(
        [sys.executable, str(PART_ROOT / "scripts" / "validate_agon_recurrence_adapter.py")],
        cwd=find_repo_root(Path(__file__).resolve()),
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
