from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aoa_sdk.recurrence.models import (  # noqa: E402
    BeaconEntry,
    BeaconPacket,
    ConnectivityGap,
    ConnectivityGapReport,
    PlanStep,
    PropagationPlan,
    ReturnHandoff,
    ReturnTarget,
    ReviewQueue,
    ReviewQueueItem,
)
from aoa_sdk.recurrence.projections import (  # noqa: E402
    build_downstream_projection_bundle,
    build_kag_projection,
    build_projection_guard_report,
    build_routing_projection,
    build_stats_projection,
)


def workspace() -> SimpleNamespace:
    return SimpleNamespace(root="/srv/workspace", repo_roots={})


def plan() -> PropagationPlan:
    return PropagationPlan(
        plan_ref="plan:test",
        signal_ref="signal:test",
        workspace_root="/srv/workspace",
        direct_components=["component:skills:trigger-evals"],
        impacted_components=[
            "component:skills:trigger-evals",
            "component:kag:donor-refresh",
        ],
        ordered_steps=[
            PlanStep(
                step_ref="step:skills:trigger-evals",
                order=1,
                component_ref="component:skills:trigger-evals",
                owner_repo="aoa-skills",
                action="revalidate",
                reason="trigger boundary changed",
                surface_refs=["docs/TRIGGER_EVALS.md"],
            ),
            PlanStep(
                step_ref="step:kag:donor-refresh",
                order=2,
                component_ref="component:kag:donor-refresh",
                owner_repo="aoa-kag",
                action="reground",
                reason="derived donor needs source return",
                surface_refs=["generated/return_regrounding_pack.min.json"],
            ),
        ],
    )


def gap_report() -> ConnectivityGapReport:
    return ConnectivityGapReport(
        report_ref="doctor:test",
        workspace_root="/srv/workspace",
        signal_ref="signal:test",
        components_checked=["component:skills:trigger-evals"],
        gaps=[
            ConnectivityGap(
                gap_ref="gap:kag:donor",
                severity="medium",
                gap_kind="unresolved_edge",
                component_ref="component:kag:donor-refresh",
                owner_repo="aoa-kag",
                evidence_refs=["generated/return_regrounding_pack.min.json"],
                recommendation="derived KAG donor needs regrounding toward owner source refs",
            )
        ],
    )


def handoff() -> ReturnHandoff:
    return ReturnHandoff(
        handoff_ref="handoff:test",
        plan_ref="plan:test",
        reviewed=True,
        targets=[
            ReturnTarget(
                owner_repo="aoa-techniques",
                component_ref="component:techniques:intake",
                target="docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md",
                target_kind="docs",
                reason="candidate pressure belongs to technique owner review",
            )
        ],
    )


def beacon_packet() -> BeaconPacket:
    return BeaconPacket(
        packet_ref="beacons:test",
        workspace_root="/srv/workspace",
        entries=[
            BeaconEntry(
                beacon_ref="beacon:overclaim",
                kind="overclaim_alarm",
                status="candidate",
                component_ref="component:evals:runtime-proof",
                owner_repo="aoa-evals",
                target_repo="aoa-evals",
                reason="runtime evidence sounded stronger than proof boundary",
                source_inputs=["docs/RUNTIME_BENCH_PROMOTION_GUIDE.md"],
            )
        ],
    )


def review_queue() -> ReviewQueue:
    return ReviewQueue(
        queue_ref="review:test",
        workspace_root="/srv/workspace",
        items=[
            ReviewQueueItem(
                item_ref="review-item:skill-gap",
                lane="skill",
                priority="medium",
                target_repo="aoa-skills",
                owner_repo="aoa-skills",
                component_ref="component:skills:trigger-evals",
                beacon_ref="beacon:skill-gap",
                kind="unused_skill_opportunity",
                status="watch",
                decision_surface="docs/TRIGGER_EVALS.md",
                summary="skill might fit but was not used",
            )
        ],
    )


def test_routing_projection_is_advisory_and_thin() -> None:
    projection = build_routing_projection(
        workspace(),
        plan=plan(),
        gap_report=gap_report(),
        return_handoff=handoff(),
        review_queue=review_queue(),
    )
    assert projection.owner_hints
    assert projection.return_hints
    assert projection.gap_hints
    assert all(hint.advisory_only is True for hint in projection.owner_hints)
    assert not any(
        "graph_snapshot" in ref
        for hint in projection.owner_hints
        for ref in hint.source_refs
    )
    schema = json.loads(
        (ROOT / "schemas/recurrence-routing-projection.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(projection.model_dump(mode="json"))
    invalid = projection.model_dump(mode="json")
    invalid["owner_hints"][0].pop("inspect_surfaces", None)
    invalid["owner_hints"][0].pop("source_refs", None)
    try:
        Draft202012Validator(schema).validate(invalid)
    except ValidationError:
        pass
    else:
        raise AssertionError("routing owner hints must carry source surface refs")


def test_stats_projection_is_derived_observability_only() -> None:
    projection = build_stats_projection(
        workspace(),
        gap_report=gap_report(),
        beacon_packet=beacon_packet(),
        review_queue=review_queue(),
        loaded_components=["component:skills:trigger-evals"],
    )
    assert projection.surface_strength == "derived_observability_only"
    assert projection.gaps.by_kind["unresolved_edge"] == 1
    assert projection.beacons.by_kind["overclaim_alarm"] == 1
    assert projection.review.by_kind["unused_skill_opportunity"] == 1


def test_stats_projection_no_input_path_keeps_schema_provenance() -> None:
    projection = build_stats_projection(workspace())
    assert projection.source_packet_refs == ["workspace:/srv/workspace"]
    schema = json.loads(
        (ROOT / "schemas/recurrence-stats-projection.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(projection.model_dump(mode="json"))


def test_kag_projection_regrounds_without_claiming_canon() -> None:
    projection = build_kag_projection(
        workspace(),
        plan=plan(),
        gap_report=gap_report(),
        return_handoff=handoff(),
        beacon_packet=beacon_packet(),
    )
    assert projection.donor_refresh_obligations
    assert projection.retrieval_invalidation_hints
    assert projection.source_strength_hints
    assert projection.regrounding_modes
    assert "canon authority" not in " ".join(projection.boundary_notes).lower().replace(
        "not become ", ""
    )
    schema = json.loads(
        (ROOT / "schemas/recurrence-kag-projection.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(projection.model_dump(mode="json"))
    invalid_modes = projection.model_dump(mode="json")
    invalid_modes["regrounding_modes"] = []
    try:
        Draft202012Validator(schema).validate(invalid_modes)
    except ValidationError:
        pass
    else:
        raise AssertionError("KAG projections must carry at least one regrounding mode")
    invalid_hint = projection.model_dump(mode="json")
    invalid_hint["source_strength_hints"] = [{}]
    try:
        Draft202012Validator(schema).validate(invalid_hint)
    except ValidationError:
        pass
    else:
        raise AssertionError("KAG source strength hints must be actionable")


def test_bundle_carries_guard_report_and_surface_postures() -> None:
    bundle = build_downstream_projection_bundle(
        workspace(),
        plan=plan(),
        gap_report=gap_report(),
        return_handoff=handoff(),
        beacon_packet=beacon_packet(),
        review_queue=review_queue(),
        loaded_components=["component:skills:trigger-evals"],
    )
    assert len(bundle.surfaces) >= 5
    assert {surface.target_repo for surface in bundle.surfaces} == {
        "aoa-routing",
        "aoa-stats",
        "aoa-kag",
    }
    assert not bundle.guard_report.violations


def test_guard_blocks_full_graph_routing_export() -> None:
    projection = build_routing_projection(workspace(), plan=plan())
    projection.owner_hints[0].source_refs.append(
        "generated/recurrence/graph_snapshot.full.json"
    )
    guard = build_projection_guard_report(workspace(), routing=projection)
    assert guard.violations
    assert guard.violations[0].kind == "routing_full_graph_export"
