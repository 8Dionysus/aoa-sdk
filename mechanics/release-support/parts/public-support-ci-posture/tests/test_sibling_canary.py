from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PART_ROOT / "scripts"
CANARY_MATRIX_REF = (
    "mechanics/release-support/parts/public-support-ci-posture/"
    "config/sibling_canary_matrix.json"
)
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
    matrix_path = repo_root / CANARY_MATRIX_REF
    write_matrix(matrix_path, ["aoa-skills", "aoa-playbooks"])

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = run_sibling_canary.main(
            [
                "--repo-root",
                str(repo_root),
                "--matrix",
                CANARY_MATRIX_REF,
            ]
        )

    assert exit_code == 0
    output = stdout.getvalue()
    assert "aoa-skills [ok]" in output
    assert "aoa-playbooks [ok]" in output


def test_sibling_canary_reports_incompatible_surface(workspace_root: Path) -> None:
    repo_root = workspace_root / "aoa-sdk"
    matrix_path = repo_root / CANARY_MATRIX_REF
    write_matrix(matrix_path, ["aoa-skills"])
    target = workspace_root / "aoa-skills" / "generated" / "skill_pack_profiles.resolved.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["schema_version"] = 99
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = run_sibling_canary.main(
            [
                "--repo-root",
                str(repo_root),
                "--matrix",
                CANARY_MATRIX_REF,
            ]
        )

    assert exit_code == 1
    output = stdout.getvalue()
    assert "aoa-skills [failed]" in output
    assert "aoa-skills.skill_pack_profiles.resolved" in output
