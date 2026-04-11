import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app
from aoa_sdk.workspace.roots import WORKSPACE_REQUIRED_REPOS
from tests.test_closeout import install_closeout_fixture


def _seed_bootstrap_workspace(workspace_root: Path) -> None:
    for repo in WORKSPACE_REQUIRED_REPOS:
        repo_root = workspace_root / repo
        repo_root.mkdir(parents=True, exist_ok=True)
        readme = repo_root / "README.md"
        if not readme.exists():
            readme.write_text(f"# {repo}\n", encoding="utf-8")

    foundation_path = workspace_root / "aoa-skills" / "generated" / "project_foundation_profile.min.json"
    foundation = json.loads(foundation_path.read_text(encoding="utf-8"))
    skills_root = workspace_root / "aoa-skills" / ".agents" / "skills"
    for skill_name in foundation["skills"]:
        skill_dir = skills_root / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            skill_file.write_text(f"# {skill_name}\n", encoding="utf-8")


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


def test_workspace_bootstrap_reports_missing_repos(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["workspace", "bootstrap", str(workspace_root), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["missing_required_repos"] == ["Tree-of-Sophia", "Dionysus"]
    assert payload["ready"] is False
    assert payload["executed"] is False


def test_workspace_bootstrap_execute_installs_foundation_and_agents(workspace_root: Path) -> None:
    _seed_bootstrap_workspace(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["workspace", "bootstrap", str(workspace_root), "--execute", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ready"] is True
    assert payload["executed"] is True
    assert payload["verified"] is True
    assert payload["agents_file"]["action"] == "write"
    assert (workspace_root / "AGENTS.md").exists()
    assert (workspace_root / ".agents" / "skills" / "aoa-change-protocol").is_symlink()
    assert (workspace_root / ".agents" / "skills" / "aoa-checkpoint-closeout-bridge").is_symlink()


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
            "session:test-closeout",
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


def test_skills_detect_can_emit_json(workspace_root: Path, install_host_skills) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
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
    assert payload["host_inventory_provided"] is True
    assert payload["activate_now"][0]["host_availability"]["status"] == "host-executable"
    assert payload["activate_now"][0]["host_availability"]["source"] == "workspace-install"


def test_skills_detect_can_emit_json_with_host_skill_annotation(workspace_root: Path) -> None:
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
            "--host-skill",
            "aoa-change-protocol",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["host_inventory_provided"] is True
    assert payload["activate_now"][0]["host_availability"]["status"] == "host-executable"
    assert payload["activate_now"][0]["host_availability"]["source"] == "host-skill-list"


def test_skills_dispatch_can_emit_json(workspace_root: Path, install_host_skills) -> None:
    install_host_skills(
        workspace_root,
        [
            "aoa-change-protocol",
            "aoa-approval-gate-check",
            "aoa-dry-run-first",
            "aoa-local-stack-bringup",
            "aoa-safe-infra-change",
        ],
    )
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
    assert payload["activate_now"][0]["host_availability"]["status"] == "host-executable"
    assert [item["skill_name"] for item in payload["must_confirm"]] == [
        "aoa-approval-gate-check",
        "aoa-dry-run-first",
        "aoa-local-stack-bringup",
        "aoa-safe-infra-change",
    ]
    assert all(item["host_availability"]["status"] == "host-executable" for item in payload["must_confirm"])


def test_skills_enter_writes_ingress_report(workspace_root: Path, install_host_skills) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
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
    assert payload["report"]["host_inventory_provided"] is True
    assert payload["report"]["activate_now"][0]["host_availability"]["source"] == "workspace-install"


def test_skills_guard_recovers_from_empty_runtime_session_file(workspace_root: Path) -> None:
    runner = CliRunner()
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text("", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--root",
            str(workspace_root),
            "--session-file",
            str(session_file),
            "--intent-text",
            "plan verify a bounded change",
            "--mutation-surface",
            "runtime",
            "--no-auto-checkpoint",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["report"]["activate_now"][0]["skill_name"] == "aoa-change-protocol"
    assert json.loads(session_file.read_text(encoding="utf-8"))["active_skills"][0]["name"] == "aoa-change-protocol"


def test_skills_detect_supports_checkpoint_phase(workspace_root: Path, install_host_skills) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "detect",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "checkpoint",
            "--intent-text",
            "plan verify a bounded change",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["phase"] == "checkpoint"
    assert payload["activate_now"][0]["skill_name"] == "aoa-change-protocol"


def test_skills_enter_writes_ingress_report_with_host_skill_manifest(
    workspace_root: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    manifest_path = tmp_path / "host-skills.json"
    manifest_path.write_text(
        json.dumps({"skills": ["aoa-change-protocol"]}, indent=2) + "\n",
        encoding="utf-8",
    )

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
            "--host-skill-manifest",
            str(manifest_path),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    report_path = Path(payload["report_path"])
    assert report_path.exists()
    assert payload["report"]["host_inventory_provided"] is True
    assert payload["report"]["activate_now"][0]["host_availability"]["status"] == "host-executable"
    assert payload["report"]["activate_now"][0]["host_availability"]["source"] == "host-manifest"


def test_skills_enter_rejects_non_object_host_skill_manifest(
    workspace_root: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    manifest_path = tmp_path / "host-skills.json"
    manifest_path.write_text("[]\n", encoding="utf-8")

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
            "--host-skill-manifest",
            str(manifest_path),
            "--json",
        ],
    )

    assert result.exit_code == 2
    assert "host skill manifest must be a JSON object" in result.output
    assert "AttributeError" not in result.output


def test_skills_guard_writes_pre_mutation_report(workspace_root: Path, install_host_skills) -> None:
    install_host_skills(
        workspace_root,
        [
            "aoa-approval-gate-check",
            "aoa-dry-run-first",
            "aoa-safe-infra-change",
        ],
    )
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
    assert payload["report"]["host_inventory_provided"] is True
    assert [item["host_availability"]["status"] for item in payload["report"]["must_confirm"]] == [
        "host-executable",
        "host-executable",
        "host-executable",
    ]


def test_skills_guard_reports_actionability_gaps_when_host_inventory_is_supplied(
    workspace_root: Path,
    install_host_skills,
) -> None:
    install_host_skills(
        workspace_root,
        [
            "aoa-approval-gate-check",
            "aoa-dry-run-first",
            "aoa-safe-infra-change",
        ],
    )
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
            "--host-skill",
            "aoa-change-protocol",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["report"]["host_inventory_provided"] is True
    assert payload["report"]["activate_now"] == []
    assert [item["host_availability"]["status"] for item in payload["report"]["must_confirm"]] == [
        "router-only",
        "router-only",
        "router-only",
    ]
    assert payload["report"]["actionability_gaps"] == [
        "aoa-approval-gate-check",
        "aoa-dry-run-first",
        "aoa-safe-infra-change",
    ]
