from __future__ import annotations
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(cmd):
    return subprocess.run([sys.executable, *cmd], cwd=ROOT, text=True, capture_output=True)


def test_wave7_generated_surface_is_current():
    result = run(['scripts/build_agon_wave7_recurrence_lanes.py', '--check'])
    assert result.returncode == 0, result.stderr


def test_wave7_validator_passes():
    result = run(['scripts/validate_agon_wave7_recurrence_lanes.py'])
    assert result.returncode == 0, result.stderr
