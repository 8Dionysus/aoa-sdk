import subprocess
import sys
from pathlib import Path

PART_ROOT = Path(__file__).resolve().parents[1]


def test_sdk_bindings_build_check():
    result = subprocess.run(
        [sys.executable, str(PART_ROOT / 'scripts/build_agon_duel_kernel_sdk_bindings.py'), '--check'],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def test_sdk_bindings_validate():
    result = subprocess.run(
        [sys.executable, str(PART_ROOT / 'scripts/validate_agon_duel_kernel_sdk_bindings.py')],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
