import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


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
