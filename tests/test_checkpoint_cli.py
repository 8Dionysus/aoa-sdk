import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def test_surfaces_detect_cli_supports_checkpoint_phase(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "surfaces",
            "detect",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "checkpoint",
            "--checkpoint-kind",
            "commit",
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["report"]["phase"] == "checkpoint"
    assert payload["report"]["checkpoint_kind"] == "commit"
    assert payload["report"]["checkpoint_should_capture"] is True


def test_checkpoint_cli_append_status_and_promote_handoff(workspace_root: Path) -> None:
    runner = CliRunner()

    append = runner.invoke(
        app,
        [
            "checkpoint",
            "append",
            str(workspace_root / "aoa-sdk"),
            "--kind",
            "commit",
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )
    assert append.exit_code == 0

    append_two = runner.invoke(
        app,
        [
            "checkpoint",
            "append",
            str(workspace_root / "aoa-sdk"),
            "--kind",
            "verify_green",
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )
    assert append_two.exit_code == 0

    status = runner.invoke(
        app,
        [
            "checkpoint",
            "status",
            str(workspace_root / "aoa-sdk"),
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )
    promote = runner.invoke(
        app,
        [
            "checkpoint",
            "promote",
            str(workspace_root / "aoa-sdk"),
            "--target",
            "harvest-handoff",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert status.exit_code == 0
    assert promote.exit_code == 0
    status_payload = json.loads(status.stdout)
    promote_payload = json.loads(promote.stdout)
    handoff_path = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk" / "harvest-handoff.json"
    assert status_payload["state"] == "reviewable"
    assert promote_payload["target"] == "harvest-handoff"
    assert handoff_path.exists()


def test_skills_guard_can_auto_append_checkpoint_note(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--mutation-surface",
            "code",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["checkpoint_capture"]["mode"] == "auto"
    assert payload["checkpoint_capture"]["appended"] is True
    assert payload["checkpoint_capture"]["checkpoint_kind"] == "commit"
    assert payload["checkpoint_capture"]["harvest_candidate_ids"]
    assert payload["checkpoint_capture"]["progression_candidate_ids"]
    assert payload["checkpoint_capture"]["session_end_skill_targets"]
    assert payload["checkpoint_capture"]["stats_refresh_recommended"] is True
    assert payload["checkpoint_capture"]["session_end_next_honest_move"]
    assert any(item["skill_name"] == "aoa-checkpoint-closeout-bridge" for item in payload["report"]["must_confirm"])
    assert payload["checkpoint_note"]["state"] in {"collecting", "reviewable"}
    note_path = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk" / "checkpoint-note.json"
    assert note_path.exists()


def test_skills_guard_explicit_checkpoint_kind_still_wins(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--intent-text",
            "reviewable verify-green checkpoint",
            "--mutation-surface",
            "code",
            "--checkpoint-kind",
            "verify_green",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["checkpoint_capture"]["mode"] == "explicit"
    assert payload["checkpoint_capture"]["appended"] is True
    assert payload["checkpoint_capture"]["checkpoint_kind"] == "verify_green"
    assert payload["checkpoint_note"]["state"] in {"collecting", "reviewable"}


def test_skills_guard_reports_no_checkpoint_signal_when_auto_capture_skips(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--intent-text",
            "refresh generated contracts",
            "--mutation-surface",
            "code",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["checkpoint_capture"]["mode"] == "auto"
    assert payload["checkpoint_capture"]["appended"] is False
    assert payload["checkpoint_capture"]["reason"] == "no_checkpoint_signal"
    assert payload["checkpoint_capture"]["session_end_skill_targets"] == []
    assert payload["checkpoint_capture"]["stats_refresh_recommended"] is False
    assert "checkpoint_note" not in payload


def test_skills_guard_reports_existing_session_end_targets_even_when_skip_occurs(workspace_root: Path) -> None:
    runner = CliRunner()

    first = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--mutation-surface",
            "code",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )
    assert first.exit_code == 0

    result = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--intent-text",
            "refresh generated contracts",
            "--mutation-surface",
            "code",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["checkpoint_capture"]["appended"] is False
    assert payload["checkpoint_capture"]["reason"] == "no_checkpoint_signal"
    assert [target["skill_name"] for target in payload["checkpoint_capture"]["session_end_skill_targets"]] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    assert payload["checkpoint_capture"]["progression_axis_signals"]
    assert payload["checkpoint_capture"]["stats_refresh_recommended"] is True
    assert payload["checkpoint_capture"]["session_end_next_honest_move"]
    assert payload["checkpoint_note"]["session_end_recommendation"] == "harvest_progression_and_upgrade"


def test_skills_guard_auto_captures_explicit_commit_growth(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--intent-text",
            "commit bounded patch",
            "--mutation-surface",
            "code",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["checkpoint_capture"]["mode"] == "auto"
    assert payload["checkpoint_capture"]["appended"] is True
    assert payload["checkpoint_capture"]["checkpoint_kind"] == "commit"
    assert any(cluster["candidate_kind"] == "growth" for cluster in payload["checkpoint_note"]["candidate_clusters"])


def test_skills_guard_can_disable_auto_checkpoint(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--mutation-surface",
            "code",
            "--no-auto-checkpoint",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["checkpoint_capture"]["appended"] is False
    assert payload["checkpoint_capture"]["reason"] == "auto_disabled"
    assert payload["checkpoint_capture"]["attempted"] is False
    assert "checkpoint_note" not in payload


def test_surfaces_detect_cli_can_append_checkpoint_note(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "surfaces",
            "detect",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "checkpoint",
            "--checkpoint-kind",
            "commit",
            "--append-note",
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["report"]["phase"] == "checkpoint"
    assert payload["checkpoint_note"]["promotion_recommendation"] in {
        "local_note",
        "dionysus_note",
        "harvest_handoff",
    }


def test_checkpoint_build_closeout_context_cli_emits_json(workspace_root: Path) -> None:
    runner = CliRunner()
    seed = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--mutation-surface",
            "code",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )
    assert seed.exit_code == 0
    seed_payload = json.loads(seed.stdout)
    session_ref = seed_payload["checkpoint_note"]["session_ref"]
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-closeout.md"
    reviewed_artifact.parent.mkdir(parents=True, exist_ok=True)
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                f"Session ref: `{session_ref}`",
                "",
                "- recurring route evidence remained visible",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "checkpoint",
            "build-closeout-context",
            str(workspace_root / "aoa-sdk"),
            "--reviewed-artifact",
            str(reviewed_artifact),
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["session_ref"] == session_ref
    assert payload["orchestrator_skill_name"] == "aoa-checkpoint-closeout-bridge"
    assert payload["ordered_skill_plan"]
    assert [item["skill_name"] for item in payload["ordered_skill_plan"]] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]


def test_checkpoint_execute_closeout_chain_cli_emits_execution_report(workspace_root: Path) -> None:
    runner = CliRunner()
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-closeout-exec.md"
    reviewed_artifact.parent.mkdir(parents=True, exist_ok=True)
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                "Session ref: `session:test-checkpoint-execute-cli`",
                "",
                "- verify green completed",
                "- repeated route remained visible",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "checkpoint",
            "execute-closeout-chain",
            str(workspace_root / "aoa-sdk"),
            "--reviewed-artifact",
            str(reviewed_artifact),
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["session_ref"] == "session:test-checkpoint-execute-cli"
    assert payload["orchestrator_skill_name"] == "aoa-checkpoint-closeout-bridge"
    assert [item["skill_name"] for item in payload["executed_skills"]] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    assert payload["produced_receipt_refs"]
