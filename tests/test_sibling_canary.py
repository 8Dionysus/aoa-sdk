from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_sibling_canary  # noqa: E402


def write_matrix(path: Path, repos: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "matrix_version": 1,
                "entries": [
                    {
                        "repo": repo,
                        "target_ref": "main",
                        "purpose": f"fixture check for {repo}",
                    }
                    for repo in repos
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_sibling_canary_reports_success_for_fixture_workspace(workspace_root: Path) -> None:
    repo_root = workspace_root / "aoa-sdk"
    matrix_path = repo_root / "scripts" / "sibling_canary_matrix.json"
    write_matrix(matrix_path, ["aoa-skills", "aoa-playbooks"])

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = run_sibling_canary.main(
            [
                "--repo-root",
                str(repo_root),
                "--matrix",
                "scripts/sibling_canary_matrix.json",
            ]
        )

    assert exit_code == 0
    output = stdout.getvalue()
    assert "aoa-skills [ok]" in output
    assert "aoa-playbooks [ok]" in output


def test_sibling_canary_reports_incompatible_surface(workspace_root: Path) -> None:
    repo_root = workspace_root / "aoa-sdk"
    matrix_path = repo_root / "scripts" / "sibling_canary_matrix.json"
    write_matrix(matrix_path, ["aoa-skills"])
    target = workspace_root / "aoa-skills" / "generated" / "runtime_discovery_index.json"
    target.write_text(
        target.read_text(encoding="utf-8").replace('"schema_version": 1', '"schema_version": 99'),
        encoding="utf-8",
    )

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = run_sibling_canary.main(
            [
                "--repo-root",
                str(repo_root),
                "--matrix",
                "scripts/sibling_canary_matrix.json",
            ]
        )

    assert exit_code == 1
    assert "aoa-skills [failed]" in stdout.getvalue()
