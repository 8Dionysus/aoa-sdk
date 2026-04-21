import subprocess
import sys


def test_sdk_bindings_build_check():
    result = subprocess.run([sys.executable, 'scripts/build_agon_duel_kernel_sdk_bindings.py', '--check'], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_sdk_bindings_validate():
    result = subprocess.run([sys.executable, 'scripts/validate_agon_duel_kernel_sdk_bindings.py'], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
