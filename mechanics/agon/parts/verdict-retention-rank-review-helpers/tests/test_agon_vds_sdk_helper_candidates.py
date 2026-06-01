from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_registry_build_clean():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_agon_vds_sdk_helper_candidates.py"),
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_registry_validates():
    data = load(
        ROOT / "scripts" / "validate_agon_vds_sdk_helper_candidates.py"
    ).validate()
    assert data["helper_count"] >= 6
