import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app
from tests.test_closeout import install_closeout_fixture


def test_workspace_inspect_reports_manifest_and_repo_paths(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["workspace", "inspect", str(workspace_root / "aoa-sdk")])

    assert result.exit_code == 0
    assert f"manifest: {(workspace_root / 'aoa-sdk' / '.aoa' / 'workspace.toml').resolve()}" in result.stdout
    assert f"aoa-sdk: {(workspace_root / 'aoa-sdk').resolve()} [federation-root]" in result.stdout


def test_workspace_inspect_can_emit_json(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["workspace", "inspect", str(workspace_root / "aoa-sdk"), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["manifest"] == str(
        (workspace_root / "aoa-sdk" / ".aoa" / "workspace.toml").resolve()
    )
    assert payload["repos"]["aoa-sdk"]["origin"] == "federation-root"


def test_compatibility_check_can_emit_repo_filtered_json(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "compatibility",
            "check",
            str(workspace_root / "aoa-sdk"),
            "--repo",
            "aoa-skills",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["repo"] == "aoa-skills"
    assert payload["compatible"] is True
    assert payload["checks"]
    assert all(entry["repo"] == "aoa-skills" for entry in payload["checks"])


def test_compatibility_check_can_emit_kag_repo_filtered_json(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "compatibility",
            "check",
            str(workspace_root / "aoa-sdk"),
            "--repo",
            "aoa-kag",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["repo"] == "aoa-kag"
    assert payload["compatible"] is True
    assert payload["checks"]
    assert all(entry["repo"] == "aoa-kag" for entry in payload["checks"])


def test_closeout_enqueue_current_can_emit_json(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "closeout",
            "enqueue-current",
            str(fixture["manifest_path"]),
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["closeout_id"] == "closeout-test-001"
    assert payload["queue_depth"] == 2
    assert payload["queued_manifest_path"].endswith(
        ".aoa/closeout/inbox/closeout-test-001.json"
    )


def test_closeout_build_manifest_can_emit_json(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "closeout",
            "build-manifest",
            str(fixture["build_request_path"]),
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--enqueue",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["closeout_id"] == "closeout-build-001"
    assert payload["manifest_path"].endswith(
        ".aoa/closeout/manifests/closeout-build-001.json"
    )
    assert payload["enqueue_report"]["queue_depth"] == 2


def test_closeout_submit_reviewed_can_emit_json(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "closeout",
            "submit-reviewed",
            str(fixture["reviewed_artifact_path"]),
            "--session-ref",
            "session:test-submit-reviewed",
            "--receipt-path",
            str(fixture["skill_receipt_path"]),
            "--receipt-path",
            str(fixture["core_skill_receipt_path"]),
            "--receipt-path",
            str(fixture["eval_receipt_path"]),
            "--audit-ref",
            str(fixture["route_summary_path"]),
            "--closeout-id",
            "closeout-submit-cli-001",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--no-enqueue",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["closeout_id"] == "closeout-submit-cli-001"
    assert payload["request_path"].endswith(
        ".aoa/closeout/requests/closeout-submit-cli-001.request.json"
    )
    assert payload["detected_publishers"] == [
        "aoa-evals.eval-result",
        "aoa-skills.core-kernel-applications",
        "aoa-skills.session-harvest-family",
    ]
    assert payload["build_report"]["manifest_path"].endswith(
        ".aoa/closeout/manifests/closeout-submit-cli-001.json"
    )
    assert payload["build_report"]["enqueue_report"] is None


def test_closeout_submit_reviewed_allow_empty_can_emit_json(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "closeout",
            "submit-reviewed",
            str(fixture["reviewed_artifact_path"]),
            "--session-ref",
            "session:test-submit-reviewed-audit-only",
            "--audit-ref",
            str(fixture["route_summary_path"]),
            "--closeout-id",
            "closeout-submit-cli-audit-only-001",
            "--allow-empty",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--no-enqueue",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["closeout_id"] == "closeout-submit-cli-audit-only-001"
    assert payload["audit_only"] is True
    assert payload["receipt_paths"] == []
    assert payload["detected_publishers"] == []


def test_closeout_run_prints_kernel_next_brief(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "closeout",
            "run",
            str(fixture["manifest_path"]),
            "--root",
            str(workspace_root / "aoa-sdk"),
        ],
    )

    assert result.exit_code == 0
    assert "kernel_next:" in result.stdout
    assert "action: invoke-core-skill" in result.stdout
    assert "skill: aoa-automation-opportunity-scan" in result.stdout


def test_closeout_process_inbox_prints_kernel_next_brief(workspace_root: Path) -> None:
    install_closeout_fixture(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "closeout",
            "process-inbox",
            str(workspace_root / "aoa-sdk"),
        ],
    )

    assert result.exit_code == 0
    assert "kernel_next:" in result.stdout
    assert "skill: aoa-automation-opportunity-scan" in result.stdout


def test_skills_detect_can_emit_json(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "detect",
            str(workspace_root / "aoa-sdk"),
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "ingress",
            "--intent-text",
            "plan verify a bounded change",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["foundation_id"] == "project-foundation-v1"
    assert payload["activate_now"][0]["skill_name"] == "aoa-change-protocol"


def test_skills_dispatch_can_emit_json(workspace_root: Path) -> None:
    runner = CliRunner()
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"

    result = runner.invoke(
        app,
        [
            "skills",
            "dispatch",
            str(workspace_root / "aoa-sdk"),
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "pre-mutation",
            "--intent-text",
            "plan verify a bounded change",
            "--mutation-surface",
            "runtime",
            "--session-file",
            str(session_file),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["activate_now"][0]["skill_name"] == "aoa-change-protocol"
    assert [item["skill_name"] for item in payload["must_confirm"]] == [
        "aoa-approval-gate-check",
        "aoa-dry-run-first",
        "aoa-local-stack-bringup",
        "aoa-safe-infra-change",
    ]


def test_skills_enter_writes_ingress_report(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "enter",
            str(workspace_root),
            "--root",
            str(workspace_root),
            "--intent-text",
            "plan verify a bounded change",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    report_path = Path(payload["report_path"])
    assert report_path.exists()
    assert report_path.name == "workspace.ingress.latest.json"
    assert payload["report"]["foundation_id"] == "project-foundation-v1"


def test_skills_guard_writes_pre_mutation_report(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--root",
            str(workspace_root),
            "--intent-text",
            "refresh generated contracts",
            "--mutation-surface",
            "repo-config",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    report_path = Path(payload["report_path"])
    assert report_path.exists()
    assert report_path.name == "aoa-sdk.pre-mutation-repo-config.latest.json"
    assert [item["skill_name"] for item in payload["report"]["must_confirm"]] == [
        "aoa-approval-gate-check",
        "aoa-dry-run-first",
        "aoa-safe-infra-change",
    ]
