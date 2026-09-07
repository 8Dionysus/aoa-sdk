from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aoa_sdk import AoASDK
from aoa_sdk.cli.main import app
from aoa_sdk.checkpoints import candidate_intelligence
from aoa_sdk.models import ExistingWrapperFit


@pytest.fixture(autouse=True)
def _explicit_runtime_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AOA_SESSION_ID", "runtime-candidate-intelligence-tests")


def _signature_by_action(report, action: str):  # type: ignore[no-untyped-def]
    return next(signature for signature in report.action_signatures if signature.action == action)


@pytest.fixture
def strong_existing_fits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate novelty from the separate, unchanged fit-classification policy."""
    def fits(*, signatures, **_kwargs):  # type: ignore[no-untyped-def]
        return {
            signature.signature_id: ExistingWrapperFit(
                wrapper_family=signature.wrapper_family_hint,
                fit_status="strong", existing_surface_ref="fixture:existing-wrapper",
                nearest_existing_wrapper="fixture:existing-wrapper",
                fit_reason="fixture supplies a strong existing fit",
                evidence_refs=list(signature.evidence_refs),
            )
            for signature in signatures
        }
    monkeypatch.setattr(candidate_intelligence, "_existing_fits", fits)


def _write_legacy_checkpoint_entry(note_dir: Path, *, observed_at: str) -> None:
    note_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_ref": "session:legacy-candidate-intelligence",
        "runtime_session_id": "runtime-legacy-candidate-intelligence",
        "runtime_session_created_at": "2026-04-10T13:55:00Z",
        "repo_root": str(note_dir.parents[3].resolve()),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "manual",
            "observed_at": observed_at,
            "report_ref": str(note_dir / "legacy-report.json"),
            "intent_text": "legacy recurring workflow candidate",
            "checkpoint_should_capture": True,
            "blocked_by": [],
            "candidate_clusters": [
                {
                    "candidate_id": "candidate:route:aoa-playbooks-playbook-registry-min",
                    "candidate_kind": "route",
                    "owner_hint": "aoa-playbooks",
                    "display_name": "Recurring route candidate",
                    "source_surface_ref": "aoa-playbooks.playbook_registry.min",
                    "evidence_refs": [
                        "aoa-playbooks.playbook_registry.min",
                        "aoa-playbooks:legacy-review",
                    ],
                    "confidence": "medium",
                    "session_end_targets": ["harvest", "progression", "upgrade"],
                    "progression_axis_signals": [],
                    "next_owner_moves": [
                        "carry the candidate through reviewed session closeout before moving candidates or stats"
                    ],
                }
            ],
            "manual_review_requested": False,
        },
    }
    with (note_dir / "checkpoint-note.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def test_checkpoint_surface_detection_emits_action_facets_and_signature_refs(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
        declared_signals=["scenario-recurring", "repeated-pattern", "proof-need", "recall-need", "role-posture"],
    )

    assert report.action_events
    assert report.action_signatures
    assert {signature.wrapper_family_hint for signature in report.action_signatures} >= {
        "eval",
        "memo",
        "owner_local",
        "playbook",
        "technique",
    }
    assert {
        event.facets.family
        for event in report.action_events
    } >= {
        "command_execution",
        "context_memory",
        "owner_routing",
        "verification",
    }
    assert all(event.facets.phase == "checkpoint" for event in report.action_events)
    assert all(event.action_signature_ref for event in report.action_events)
    assert all(cluster.action_signature_refs for cluster in report.candidate_clusters)


def test_checkpoint_candidate_intelligence_counts_repetition_after_deduping_events(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    intent_text = "recurring workflow needs better handoff proof and recall"

    first = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
        declared_signals=["scenario-recurring", "proof-need", "recall-need"],
    )
    assert first.repetition_clusters
    assert {
        cluster.wrapper_readiness.draftability
        for cluster in first.repetition_clusters
    } == {"observe"}
    assert all(cluster.repeat_count == 1 for cluster in first.repetition_clusters)
    assert all(
        "no_single_event_promotion" in cluster.wrapper_readiness.stop_lines
        for cluster in first.repetition_clusters
    )

    second = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
        declared_signals=["scenario-recurring", "proof-need", "recall-need"],
    )

    assert all(cluster.repeat_count == 2 for cluster in second.repetition_clusters)
    assert {
        cluster.wrapper_readiness.draftability
        for cluster in second.repetition_clusters
    } == {"reviewable"}
    assert all(
        cluster.wrapper_readiness.draftability != "draftable"
        for cluster in second.repetition_clusters
    )
    assert len(second.action_events) < sum(
        len(entry.action_events) for entry in second.checkpoint_history
    )


@pytest.mark.parametrize("intent", ["Do not create a new wrapper", "We need a new wrapper", 'Quote: "new wrapper"'])
def test_words_do_not_override_strong_existing_wrapper_fit(workspace_root: Path, intent: str, strong_existing_fits: None) -> None:
    report = AoASDK.from_workspace(workspace_root / "aoa-sdk").surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"), phase="checkpoint",
        intent_text=intent, declared_signals=["scenario-recurring"],
    )
    assert report.action_signatures
    assert report.wrapper_gap_candidates == []


def test_reasoned_novelty_is_scoped_to_an_observed_signature(workspace_root: Path, strong_existing_fits: None) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    args = dict(
        repo_root=str(workspace_root / "aoa-sdk"), phase="checkpoint",
        declared_signals=["scenario-recurring", "proof-need"],
    )
    baseline = sdk.surfaces.detect(**args)
    signature = _signature_by_action(baseline, "repeat_manual_workflow")
    reason = "Existing route lacks the required reversible multi-owner handoff boundary."
    report = sdk.surfaces.detect(**args, wrapper_novelty_reasons={signature.signature_id: reason})
    assert len(report.wrapper_gap_candidates) == 1
    gap = report.wrapper_gap_candidates[0]
    assert gap.signature_id == signature.signature_id
    assert gap.draftability == "reviewable"
    assert reason in gap.novelty_reason
    assert gap.evidence_refs == signature.evidence_refs
    for reasons in ({"signature:unknown": reason}, {signature.signature_id: " "}):
        with pytest.raises(ValueError):
            sdk.surfaces.detect(**args, wrapper_novelty_reasons=reasons)


def test_checkpoint_candidate_intelligence_backfills_legacy_candidate_clusters(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AOA_SESSION_ID", "runtime-legacy-candidate-intelligence"
    )
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    note_dir = (
        workspace_root
        / "aoa-sdk"
        / ".aoa"
        / "session-growth"
        / "current"
        / "runtime-legacy-candidate-intelligence"
        / "aoa-sdk"
    )
    _write_legacy_checkpoint_entry(note_dir, observed_at="2026-04-10T14:00:00Z")
    _write_legacy_checkpoint_entry(note_dir, observed_at="2026-04-10T14:01:00Z")

    report = sdk.checkpoints.candidate_intelligence(
        repo_root=str(workspace_root / "aoa-sdk"),
        sample_limit=1,
    )

    signature = _signature_by_action(report, "repeat_manual_workflow")
    cluster = next(item for item in report.repetition_clusters if item.signature_id == signature.signature_id)
    assert signature.wrapper_family_hint == "playbook"
    assert signature.event_types == ["repeated_manual_workflow_candidate"]
    assert "route_signal:legacy_backfill" in signature.route_signals
    assert "single_event_cannot_promote" not in signature.negative_evidence
    assert cluster.repeat_count == 2
    assert cluster.wrapper_readiness.draftability == "reviewable"
    assert report.sample_audit[0].verdict == "unreviewed"


def test_checkpoint_candidate_intelligence_enriches_legacy_flat_signatures(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AOA_SESSION_ID", "runtime-legacy-flat-signatures")
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    note_dir = (
        workspace_root
        / "aoa-sdk"
        / ".aoa"
        / "session-growth"
        / "current"
        / "runtime-legacy-flat-signatures"
        / "aoa-sdk"
    )
    note_dir.mkdir(parents=True, exist_ok=True)
    surface = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
    )
    flat_signatures = []
    for signature in surface.action_signatures:
        payload = signature.model_dump(mode="json")
        payload.update(
            {
                "event_types": [],
                "route_signals": [],
                "mutation_surfaces": [],
                "authority_surfaces": [],
                "memory_provenance_refs": [],
                "negative_evidence": [],
            }
        )
        if payload["action"] == "record_commit_mutation":
            payload["action_event_ids"] = [
                *payload["action_event_ids"],
                "action-event:legacy-second-commit-mutation",
            ]
        flat_signatures.append(payload)
    payload = {
        "session_ref": "session:legacy-flat-signatures",
        "runtime_session_id": "runtime-legacy-flat-signatures",
        "runtime_session_created_at": "2026-04-10T13:55:00Z",
        "repo_root": str((workspace_root / "aoa-sdk").resolve()),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "commit",
            "observed_at": "2026-04-10T14:00:00Z",
            "report_ref": str(note_dir / "legacy-flat-report.json"),
            "intent_text": "legacy flat signatures still carry events",
            "checkpoint_should_capture": True,
            "blocked_by": [],
            "candidate_clusters": [cluster.model_dump(mode="json") for cluster in surface.candidate_clusters],
            "action_events": [event.model_dump(mode="json") for event in surface.action_events],
            "action_signatures": flat_signatures,
            "manual_review_requested": False,
        },
    }
    with (note_dir / "checkpoint-note.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

    report = sdk.checkpoints.candidate_intelligence(
        repo_root=str(workspace_root / "aoa-sdk"),
        sample_limit=1,
    )

    signature = _signature_by_action(report, "record_commit_mutation")
    assert signature.event_types == ["commit_mutation_action"]
    assert "route_signal:mutation_surface" in signature.route_signals
    assert signature.mutation_surfaces == ["code"]
    assert "aoa-sdk" in signature.authority_surfaces
    assert "single_event_cannot_promote" not in signature.negative_evidence


def test_checkpoint_candidate_intelligence_counts_duplicate_saved_signature_refs(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AOA_SESSION_ID", "runtime-legacy-duplicate-saved-signatures"
    )
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    note_dir = (
        workspace_root
        / "aoa-sdk"
        / ".aoa"
        / "session-growth"
        / "current"
        / "runtime-legacy-duplicate-saved-signatures"
        / "aoa-sdk"
    )
    note_dir.mkdir(parents=True, exist_ok=True)
    surface = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
    )
    saved_signature = _signature_by_action(surface, "record_commit_mutation")
    event_refs = [
        saved_signature.action_event_ids[0],
        "action-event:legacy-second-commit-mutation",
    ]
    duplicate_signatures = []
    for event_ref in event_refs:
        payload = saved_signature.model_dump(mode="json")
        payload["action_event_ids"] = [event_ref]
        payload["negative_evidence"] = ["single_event_cannot_promote"]
        duplicate_signatures.append(payload)
    payload = {
        "session_ref": "session:legacy-duplicate-saved-signatures",
        "runtime_session_id": "runtime-legacy-duplicate-saved-signatures",
        "runtime_session_created_at": "2026-04-10T13:55:00Z",
        "repo_root": str((workspace_root / "aoa-sdk").resolve()),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "commit",
            "observed_at": "2026-04-10T14:00:00Z",
            "report_ref": str(note_dir / "legacy-duplicate-saved-signatures-report.json"),
            "intent_text": "legacy duplicate signatures still carry distinct saved event refs",
            "checkpoint_should_capture": True,
            "blocked_by": [],
            "candidate_clusters": [cluster.model_dump(mode="json") for cluster in surface.candidate_clusters],
            "action_events": [],
            "action_signatures": duplicate_signatures,
            "manual_review_requested": False,
        },
    }
    with (note_dir / "checkpoint-note.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

    report = sdk.checkpoints.candidate_intelligence(
        repo_root=str(workspace_root / "aoa-sdk"),
        sample_limit=1,
    )

    signature = _signature_by_action(report, "record_commit_mutation")
    cluster = next(item for item in report.repetition_clusters if item.signature_id == signature.signature_id)
    assert signature.action_event_ids == event_refs
    assert "single_event_cannot_promote" not in signature.negative_evidence
    assert cluster.repeat_count == 2


def test_checkpoint_candidate_intelligence_preserves_repeated_saved_signature_refs(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AOA_SESSION_ID", "runtime-legacy-repeated-saved-signature-refs"
    )
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    note_dir = (
        workspace_root
        / "aoa-sdk"
        / ".aoa"
        / "session-growth"
        / "current"
        / "runtime-legacy-repeated-saved-signature-refs"
        / "aoa-sdk"
    )
    note_dir.mkdir(parents=True, exist_ok=True)
    surface = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
    )
    saved_signature = _signature_by_action(surface, "record_commit_mutation")
    event_ref = saved_signature.action_event_ids[0]
    payload = saved_signature.model_dump(mode="json")
    payload["action_event_ids"] = [event_ref, event_ref]
    payload["negative_evidence"] = ["single_event_cannot_promote"]
    checkpoint_entry = {
        "session_ref": "session:legacy-repeated-saved-signature-refs",
        "runtime_session_id": "runtime-legacy-repeated-saved-signature-refs",
        "runtime_session_created_at": "2026-04-10T13:55:00Z",
        "repo_root": str((workspace_root / "aoa-sdk").resolve()),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "commit",
            "observed_at": "2026-04-10T14:00:00Z",
            "report_ref": str(note_dir / "legacy-repeated-saved-signature-refs-report.json"),
            "intent_text": "legacy saved signature still carries repeated event refs",
            "checkpoint_should_capture": True,
            "blocked_by": [],
            "candidate_clusters": [cluster.model_dump(mode="json") for cluster in surface.candidate_clusters],
            "action_events": [],
            "action_signatures": [payload],
            "manual_review_requested": False,
        },
    }
    with (note_dir / "checkpoint-note.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(checkpoint_entry, ensure_ascii=True) + "\n")

    report = sdk.checkpoints.candidate_intelligence(
        repo_root=str(workspace_root / "aoa-sdk"),
        sample_limit=1,
    )

    signature = _signature_by_action(report, "record_commit_mutation")
    cluster = next(item for item in report.repetition_clusters if item.signature_id == signature.signature_id)
    assert signature.action_event_ids == [event_ref, event_ref]
    assert "single_event_cannot_promote" not in signature.negative_evidence
    assert cluster.repeat_count == 2


def test_checkpoint_candidate_intelligence_classifies_wrapper_lanes_and_gap_pressure(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    eval_report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="manual",
        intent_text="verify regression proof invariant quality",
        declared_signals=["proof-need"],
    )
    memo_report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="manual",
        intent_text="memory recall prior provenance",
        declared_signals=["recall-need"],
    )
    owner_report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="manual",
        intent_text="agent role owner boundary",
        declared_signals=["role-posture"],
    )
    risk_note = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text="risk gate hidden automation requires confirmation",
    )
    gap_report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="manual",
        intent_text="нет существующего aoa для этой операции",
    )

    assert _signature_by_action(eval_report, "define_bounded_verification").wrapper_family_hint == "eval"
    assert _signature_by_action(memo_report, "retrieve_prior_context").wrapper_family_hint == "memo"
    assert _signature_by_action(owner_report, "clarify_owner_or_agent_role").wrapper_family_hint == "owner_local"
    assert risk_note.repetition_clusters[0].wrapper_readiness.draftability == "blocked"
    assert "automation_risk_requires_review" in risk_note.repetition_clusters[0].wrapper_readiness.blockers
    assert "risk_signal_requires_review" in risk_note.action_signatures[0].negative_evidence
    assert gap_report.action_signatures == []
    assert gap_report.wrapper_gap_candidates == []


def test_checkpoint_candidate_intelligence_cli_writes_generated_navigation_index(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    intent_text = "recurring workflow needs better handoff proof and recall"
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
        declared_signals=["scenario-recurring", "repeated-pattern", "proof-need", "recall-need", "role-posture"],
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
    )

    result = CliRunner().invoke(
        app,
        [
            "checkpoint",
            "candidate-intelligence",
            str(workspace_root / "aoa-sdk"),
            "--sample-limit",
            "2",
            "--write-index",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    index_ref = Path(payload["generated_index_ref"])
    assert payload["report_type"] == "checkpoint_candidate_intelligence_report_v1"
    assert payload["source"] == "checkpoint_note"
    assert len(payload["sample_audit"]) == 2
    assert index_ref.exists()

    index = json.loads(index_ref.read_text(encoding="utf-8"))
    assert index["artifact_type"] == "checkpoint_candidate_intelligence_navigation_index_v1"
    assert "not reviewed memory" in index["boundary_note"]
    assert index["counts"]["repetition_clusters"] == len(payload["repetition_clusters"])
    assert index["counts"]["graph_anchors"] > 0
    assert index["counts"]["graph_edges"] > 0
    assert set(index["by_wrapper_family"]) >= {"eval", "memo", "owner_local", "playbook", "technique"}
    assert "repeated_manual_workflow_candidate" in index["by_event_type"]
    assert "route copied without owner review" in index["by_negative_evidence"]
