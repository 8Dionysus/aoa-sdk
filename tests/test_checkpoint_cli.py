import json
from datetime import datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aoa_sdk.cli.main import app


@pytest.fixture(autouse=True)
def _clear_codex_thread_id(monkeypatch) -> None:
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)


def _checkpoint_note_dir(
    workspace_root: Path,
    *,
    repo_label: str,
    runtime_session_id: str | None = None,
) -> Path:
    current_root = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current"
    if runtime_session_id is None:
        return current_root / repo_label
    return current_root / runtime_session_id / repo_label


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
    handoff_path = (
        _checkpoint_note_dir(
            workspace_root,
            repo_label="aoa-sdk",
            runtime_session_id=status_payload["runtime_session_id"],
        )
        / "harvest-handoff.json"
    )
    assert status_payload["state"] == "reviewable"
    assert status_payload["checkpoint_history"][-1]["observed_at_local"]
    assert status_payload["checkpoint_history"][-1]["observed_tz"]
    assert promote_payload["target"] == "harvest-handoff"
    assert promote_payload["promoted_at_local"]
    assert promote_payload["promoted_tz"]
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
    assert payload["checkpoint_capture"]["captured_at_local"]
    assert payload["checkpoint_capture"]["captured_tz"]
    assert payload["checkpoint_capture"]["harvest_candidate_ids"]
    assert payload["checkpoint_capture"]["progression_candidate_ids"]
    assert payload["checkpoint_capture"]["session_end_skill_targets"]
    assert payload["checkpoint_capture"]["stats_refresh_recommended"] is True
    assert payload["checkpoint_capture"]["session_end_next_honest_move"]
    assert any(item["skill_name"] == "aoa-checkpoint-closeout-bridge" for item in payload["report"]["must_confirm"])
    assert payload["checkpoint_note"]["state"] in {"collecting", "reviewable"}
    note_path = (
        _checkpoint_note_dir(
            workspace_root,
            repo_label="aoa-sdk",
            runtime_session_id=payload["checkpoint_note"]["runtime_session_id"],
        )
        / "checkpoint-note.json"
    )
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
    assert payload["checkpoint_capture"]["captured_at_local"]
    assert payload["checkpoint_capture"]["captured_tz"]
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


def test_checkpoint_status_cli_backfills_local_timestamp_for_legacy_history_entry(workspace_root: Path) -> None:
    runner = CliRunner()
    note_dir = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk"
    note_dir.mkdir(parents=True, exist_ok=True)
    legacy_payload = {
        "session_ref": "session:2026-04-09-aoa-sdk-checkpoint-growth",
        "repo_root": str(workspace_root / "aoa-sdk"),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "commit",
            "observed_at": "2026-04-09T17:54:04Z",
            "report_ref": str(note_dir / "legacy-report.json"),
            "intent_text": "legacy checkpoint",
            "checkpoint_should_capture": False,
            "blocked_by": [],
            "candidate_clusters": [],
            "manual_review_requested": False,
        },
    }
    (note_dir / "checkpoint-note.jsonl").write_text(json.dumps(legacy_payload) + "\n", encoding="utf-8")

    result = runner.invoke(
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

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    expected_local = datetime.fromisoformat("2026-04-09T17:54:04+00:00").astimezone().isoformat()
    assert payload["checkpoint_history"][0]["observed_at_local"] == expected_local
    assert payload["checkpoint_history"][0]["observed_tz"]


def test_checkpoint_status_cli_hides_stale_current_note_for_changed_runtime_session(workspace_root: Path) -> None:
    runner = CliRunner()
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "checkpoint-skill-session.json"

    append = runner.invoke(
        app,
        [
            "checkpoint",
            "append",
            str(workspace_root / "aoa-sdk"),
            "--kind",
            "commit",
            "--intent-text",
            "commit bounded patch",
            "--session-file",
            str(session_file),
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )
    assert append.exit_code == 0

    session_payload = json.loads(session_file.read_text(encoding="utf-8"))
    session_payload["session_id"] = "runtime-session-two"
    session_payload["created_at"] = "2026-04-10T12:00:00Z"
    session_payload["updated_at"] = "2026-04-10T12:00:00Z"
    session_file.write_text(json.dumps(session_payload, indent=2) + "\n", encoding="utf-8")

    status = runner.invoke(
        app,
        [
            "checkpoint",
            "status",
            str(workspace_root / "aoa-sdk"),
            "--session-file",
            str(session_file),
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert status.exit_code != 0
    assert (
        "no active checkpoint note exists yet" in status.stdout
        or "no active checkpoint note exists yet" in str(status.exception)
        or "no checkpoint note exists yet" in status.stdout
        or "no checkpoint note exists yet" in str(status.exception)
    )


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
    assert payload["checkpoint_capture"]["captured_at_local"]
    assert payload["checkpoint_capture"]["captured_tz"]
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
    assert payload["built_at_local"]
    assert payload["built_tz"]
    assert payload["ordered_skill_plan"]
    assert [item["skill_name"] for item in payload["ordered_skill_plan"]] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]


def test_checkpoint_human_cli_marks_canonical_utc_labels(workspace_root: Path) -> None:
    runner = CliRunner()

    guard = runner.invoke(
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
        ],
    )
    assert guard.exit_code == 0
    assert "checkpoint_capture_at_canonical_utc:" in guard.stdout
    assert "(local " in guard.stdout

    status_result = runner.invoke(
        app,
        [
            "checkpoint",
            "status",
            str(workspace_root / "aoa-sdk"),
            "--root",
            str(workspace_root),
            "--json",
        ],
    )
    assert status_result.exit_code == 0
    status_payload = json.loads(status_result.stdout)

    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-closeout-human.md"
    reviewed_artifact.parent.mkdir(parents=True, exist_ok=True)
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                f"Session ref: `{status_payload['session_ref']}`",
                "",
                "- verify green completed",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    context_result = runner.invoke(
        app,
        [
            "checkpoint",
            "build-closeout-context",
            str(workspace_root / "aoa-sdk"),
            "--reviewed-artifact",
            str(reviewed_artifact),
            "--root",
            str(workspace_root),
        ],
    )
    assert context_result.exit_code == 0
    assert "execution_mode: mechanical_bridge_context" in context_result.stdout
    assert "mechanical_bridge_only: yes" in context_result.stdout
    assert "agent_skill_application_required: yes" in context_result.stdout
    assert "built_at_canonical_utc:" in context_result.stdout
    assert "(local " in context_result.stdout

    execution_result = runner.invoke(
        app,
        [
            "checkpoint",
            "execute-closeout-chain",
            str(workspace_root / "aoa-sdk"),
            "--reviewed-artifact",
            str(reviewed_artifact),
            "--root",
            str(workspace_root),
        ],
    )
    assert execution_result.exit_code == 0
    assert "execution_mode: mechanical_bridge_artifact_build" in execution_result.stdout
    assert "mechanical_bridge_only: yes" in execution_result.stdout
    assert "agent_skill_application_required: yes" in execution_result.stdout
    assert "executed_at_canonical_utc:" in execution_result.stdout
    assert "(local " in execution_result.stdout


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
    assert payload["execution_mode"] == "mechanical_bridge_artifact_build"
    assert payload["mechanical_bridge_only"] is True
    assert payload["agent_skill_application_required"] is True
    assert payload["authority_contract"] == "reviewed_artifact_primary_checkpoint_hints_provisional"
    assert payload["executed_at_local"]
    assert payload["executed_tz"]
    assert [item["skill_name"] for item in payload["executed_skills"]] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    assert payload["produced_receipt_refs"]
