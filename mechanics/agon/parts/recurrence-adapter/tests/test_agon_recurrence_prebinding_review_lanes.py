from __future__ import annotations
import pathlib
import subprocess
import sys

PART_ROOT = pathlib.Path(__file__).resolve().parents[1]


def find_repo_root(start: pathlib.Path) -> pathlib.Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "aoa_sdk").is_dir():
            return candidate
    raise RuntimeError(f"could not find aoa-sdk repo root from {start}")


ROOT = find_repo_root(pathlib.Path(__file__).resolve())


def run(cmd):
    return subprocess.run([sys.executable, *cmd], cwd=ROOT, text=True, capture_output=True)


def test_prebinding_review_lane_generated_surface_is_current():
    result = run([str(PART_ROOT / 'scripts' / 'build_agon_recurrence_prebinding_review_lanes.py'), '--check'])
    assert result.returncode == 0, result.stderr


def test_prebinding_review_lane_validator_passes():
    result = run([str(PART_ROOT / 'scripts' / 'validate_agon_recurrence_prebinding_review_lanes.py')])
    assert result.returncode == 0, result.stderr
