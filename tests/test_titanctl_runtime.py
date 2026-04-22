import json
import subprocess
import sys
from pathlib import Path


def run_titanctl(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_titanctl_summon_validate_gate_closeout(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "titanctl.py"
    receipt = tmp_path / "receipt.json"

    result = run_titanctl(script, "summon", "--workspace", "/srv", "--operator", "test", "--out", str(receipt))
    assert result.returncode == 0, result.stderr

    result = run_titanctl(script, "validate", "--receipt", str(receipt))
    assert result.returncode == 0, result.stderr

    result = run_titanctl(
        script,
        "gate",
        "--receipt", str(receipt),
        "--agent", "Forge",
        "--kind", "mutation",
        "--intent", "bounded implementation test",
    )
    assert result.returncode == 0, result.stderr

    result = run_titanctl(
        script,
        "gate",
        "--receipt", str(receipt),
        "--agent", "Delta",
        "--kind", "judgment",
        "--intent", "bounded comparison test",
    )
    assert result.returncode == 0, result.stderr

    result = run_titanctl(script, "closeout", "--receipt", str(receipt), "--summary", "closed by test")
    assert result.returncode == 0, result.stderr

    data = json.loads(receipt.read_text())
    assert data["status"] == "closed"
    assert data["cohort"]["Forge"]["state"] == "active"
    assert data["cohort"]["Delta"]["state"] == "active"
