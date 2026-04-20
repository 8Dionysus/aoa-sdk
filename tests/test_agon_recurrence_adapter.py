from __future__ import annotations
import subprocess, sys
from pathlib import Path

def test_agon_recurrence_adapter_validates():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/validate_agon_recurrence_adapter.py"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
