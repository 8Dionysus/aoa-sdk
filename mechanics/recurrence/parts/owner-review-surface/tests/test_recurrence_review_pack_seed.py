from __future__ import annotations

# ruff: noqa: E402

import sys
import types


def _install_workspace_stub() -> None:
    if "aoa_sdk.workspace.discovery" in sys.modules:
        return
    workspace_pkg = types.ModuleType("aoa_sdk.workspace")
    discovery = types.ModuleType("aoa_sdk.workspace.discovery")

    class Workspace:
        def __init__(self, root=None, repo_roots=None):
            self.root = root
            self.repo_roots = repo_roots or {}

        @classmethod
        def discover(cls, root="."):
            return cls(root=root, repo_roots={})

    discovery.Workspace = Workspace
    workspace_pkg.discovery = discovery
    sys.modules["aoa_sdk.workspace"] = workspace_pkg
    sys.modules["aoa_sdk.workspace.discovery"] = discovery


_install_workspace_stub()

from aoa_sdk.recurrence.models import (
    BeaconEntry,
    BeaconPacket,
    UsageGapItem,
    UsageGapReport,
)
from aoa_sdk.recurrence.review import (
    build_candidate_dossier_packet,
    build_owner_review_summary,
    build_review_queue,
)


def test_review_queue_keeps_explicit_owner_authored_watch_usage_gaps() -> None:
    packet = BeaconPacket(
        packet_ref="beacons:test",
        workspace_root="/tmp/workspace",
        signal_ref="signal:test",
        entries=[
            BeaconEntry(
                beacon_ref="skills.owner_authored.omission_review",
                kind="unused_skill_opportunity",
                status="watch",
                component_ref="component:example:owner-authored-skill-evidence",
                owner_repo="example-skill-owner",
                target_repo="example-skill-owner",
                decision_surface="skills/example/SKILL.md",
                reason="owner-reviewed comparison marks a possible omission",
                evidence_refs=["session-evidence:reviewed-case-001"],
                source_inputs=["owner-reviewed-skill-evidence"],
                related_signals=["owner_reviewed_skill_omission"],
                suppression_flags=[],
                recommended_actions=["rerun held-out owner comparison"],
            ),
            BeaconEntry(
                beacon_ref="evals.portable_eval.runtime_pressure",
                kind="portable_eval_candidate",
                status="candidate",
                component_ref="component:evals:portable-proof-beacons",
                owner_repo="aoa-evals",
                target_repo="aoa-evals",
                decision_surface="docs/RUNTIME_BENCH_PROMOTION_GUIDE.md",
                reason="portable proof pressure has repeated",
                evidence_refs=["bench:001", "bench:002"],
                source_inputs=["runtime-candidate-guide"],
                related_signals=["portable_claim_repeat"],
                suppression_flags=[],
                recommended_actions=["open portable eval boundary review"],
            ),
        ],
    )
    usage_gaps = UsageGapReport(
        report_ref="usage:test",
        workspace_root="/tmp/workspace",
        signal_ref="signal:test",
        items=[
            UsageGapItem(
                gap_ref="usage-gap:0001",
                component_ref="component:example:owner-authored-skill-evidence",
                owner_repo="example-skill-owner",
                beacon_ref="skills.owner_authored.omission_review",
                status="watch",
                reason="owner-reviewed comparison marks a possible omission",
                decision_surface="skills/example/SKILL.md",
                evidence_refs=["session-evidence:reviewed-case-001"],
                recommended_actions=["rerun held-out owner comparison"],
            )
        ],
    )

    queue = build_review_queue(packet, usage_gaps=usage_gaps)
    assert len(queue.items) == 2
    assert any(
        item.kind == "unused_skill_opportunity" and item.priority == "medium"
        for item in queue.items
    )
    assert any(
        item.kind == "portable_eval_candidate" and item.priority == "high"
        for item in queue.items
    )


def test_dossiers_and_summary_are_grouped_by_owner() -> None:
    packet = BeaconPacket(
        packet_ref="beacons:test",
        workspace_root="/tmp/workspace",
        signal_ref="signal:test",
        entries=[
            BeaconEntry(
                beacon_ref="technique.canonical.second_consumer_pressure",
                kind="canonical_pressure",
                status="review_ready",
                component_ref="component:techniques:canon-and-intake-beacons",
                owner_repo="aoa-techniques",
                target_repo="aoa-techniques",
                decision_surface="docs/CANONICAL_RUBRIC.md",
                reason="second consumer pressure is ready for review",
                evidence_refs=["receipt:010", "receipt:011"],
                source_inputs=["technique-live-receipts"],
                related_signals=["second_consumer_confirmed"],
                suppression_flags=[],
                recommended_actions=["refresh promotion-readiness evidence"],
            )
        ],
    )
    queue = build_review_queue(packet)
    dossiers = build_candidate_dossier_packet(queue)
    summary = build_owner_review_summary(queue)

    assert len(dossiers.dossiers) == 1
    assert dossiers.dossiers[0].review_questions
    assert summary.owners[0].target_repo == "aoa-techniques"
    assert summary.owners[0].by_status["review_ready"] == 1
