"""Generated checkpoint candidate-intelligence navigation indexes."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..models import CandidateIntelligenceReport
from ..workspace.discovery import Workspace
from .naming import safe_checkpoint_name


def checkpoint_candidate_intelligence_index_path(workspace: Workspace) -> Path:
    return (
        workspace.repo_path("aoa-sdk")
        / ".aoa"
        / "session-growth"
        / "indexes"
        / "checkpoint-candidate-intelligence.min.json"
    )


def build_checkpoint_candidate_intelligence_index(
    report: CandidateIntelligenceReport,
) -> dict[str, Any]:
    signatures = sorted(report.action_signatures, key=lambda item: item.signature_id)
    clusters = sorted(report.repetition_clusters, key=lambda item: item.cluster_id)
    gaps = sorted(report.wrapper_gap_candidates, key=lambda item: item.candidate_id)
    anchors, edges = _graph_ready(report)
    return {
        "schema_version": 1,
        "artifact_type": "checkpoint_candidate_intelligence_navigation_index_v1",
        "boundary_note": (
            "Generated navigation only; action signatures and wrapper gaps are "
            "classifier route evidence, not reviewed memory, proof, owner verdict, "
            "accepted wrapper, or promotion authority."
        ),
        "repo_label": report.repo_label,
        "counts": {
            "action_events": len(report.action_events),
            "action_signatures": len(signatures),
            "repetition_clusters": len(clusters),
            "wrapper_gap_candidates": len(gaps),
            "sample_audit": len(report.sample_audit),
            "by_wrapper_family": dict(
                sorted(Counter(item.wrapper_family_hint for item in signatures).items())
            ),
            "by_draftability": dict(
                sorted(Counter(item.wrapper_readiness.draftability for item in clusters).items())
            ),
            "graph_anchors": len(anchors),
            "graph_edges": len(edges),
        },
        "action_signatures": [
            {
                "signature_id": signature.signature_id,
                "family": signature.family,
                "action": signature.action,
                "object": signature.object,
                "wrapper_family_hint": signature.wrapper_family_hint,
                "confidence": signature.confidence,
                "owner_pressure": signature.owner_pressure,
                "evidence_refs": signature.evidence_refs,
            }
            for signature in signatures
        ],
        "repetition_clusters": [
            {
                "cluster_id": cluster.cluster_id,
                "signature_id": cluster.signature_id,
                "repeat_count": cluster.repeat_count,
                "cross_session_count": cluster.cross_session_count,
                "owner_clarity": cluster.owner_clarity,
                "novelty_pressure": cluster.novelty_pressure,
                "automation_risk": cluster.automation_risk,
                "review_debt": cluster.review_debt,
                "draftability": cluster.wrapper_readiness.draftability,
                "proposed_wrapper_family": cluster.wrapper_readiness.proposed_wrapper_family,
                "existing_fit": cluster.existing_wrapper_fit.fit_status,
                "wrapper_gap": (
                    cluster.wrapper_gap.candidate_id if cluster.wrapper_gap is not None else None
                ),
            }
            for cluster in clusters
        ],
        "wrapper_gap_candidates": [
            {
                "candidate_id": gap.candidate_id,
                "signature_id": gap.signature_id,
                "proposed_wrapper_family": gap.proposed_wrapper_family,
                "nearest_existing_wrapper": gap.nearest_existing_wrapper,
                "novelty_reason": gap.novelty_reason,
                "draftability": gap.draftability,
                "review_status": gap.review_status,
                "evidence_refs": gap.evidence_refs,
            }
            for gap in gaps
        ],
        "by_signature": _by_signature(report),
        "by_wrapper_family": _group_signatures(signatures, "wrapper_family_hint"),
        "by_owner_pressure": _by_owner_pressure(signatures),
        "by_existing_fit": _by_existing_fit(clusters),
        "sample_audit": [sample.model_dump(mode="json") for sample in report.sample_audit],
        "graph_ready": {
            "anchors": anchors,
            "edges": edges,
        },
    }


def write_checkpoint_candidate_intelligence_index(
    *,
    workspace: Workspace,
    report: CandidateIntelligenceReport,
) -> Path:
    path = checkpoint_candidate_intelligence_index_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            build_checkpoint_candidate_intelligence_index(report),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _by_signature(report: CandidateIntelligenceReport) -> dict[str, dict[str, list[str]]]:
    result: dict[str, dict[str, list[str]]] = {}
    events_by_signature: dict[str, list[str]] = defaultdict(list)
    clusters_by_signature: dict[str, list[str]] = defaultdict(list)
    gaps_by_signature: dict[str, list[str]] = defaultdict(list)
    for event in report.action_events:
        if event.action_signature_ref:
            events_by_signature[event.action_signature_ref].append(event.event_id)
    for cluster in report.repetition_clusters:
        clusters_by_signature[cluster.signature_id].append(cluster.cluster_id)
    for gap in report.wrapper_gap_candidates:
        gaps_by_signature[gap.signature_id].append(gap.candidate_id)
    for signature in report.action_signatures:
        result[signature.signature_id] = {
            "events": sorted(events_by_signature.get(signature.signature_id, [])),
            "clusters": sorted(clusters_by_signature.get(signature.signature_id, [])),
            "wrapper_gaps": sorted(gaps_by_signature.get(signature.signature_id, [])),
        }
    return result


def _group_signatures(signatures, attr: str) -> dict[str, list[str]]:  # type: ignore[no-untyped-def]
    grouped: dict[str, list[str]] = defaultdict(list)
    for signature in signatures:
        grouped[str(getattr(signature, attr))].append(signature.signature_id)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _by_owner_pressure(signatures) -> dict[str, list[str]]:  # type: ignore[no-untyped-def]
    grouped: dict[str, list[str]] = defaultdict(list)
    for signature in signatures:
        for owner in signature.owner_pressure:
            grouped[owner].append(signature.signature_id)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _by_existing_fit(clusters) -> dict[str, list[str]]:  # type: ignore[no-untyped-def]
    grouped: dict[str, list[str]] = defaultdict(list)
    for cluster in clusters:
        grouped[cluster.existing_wrapper_fit.fit_status].append(cluster.cluster_id)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _graph_ready(report: CandidateIntelligenceReport) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    anchors_by_id: dict[str, dict[str, str]] = {}
    edges: list[dict[str, str]] = []
    for signature in report.action_signatures:
        signature_anchor = _anchor_id("action_signature", signature.signature_id)
        anchors_by_id[signature_anchor] = {
            "id": signature_anchor,
            "kind": "action_signature",
            "ref": signature.signature_id,
        }
        for owner in signature.owner_pressure:
            _add_edge(
                anchors_by_id,
                edges,
                source=signature_anchor,
                kind="owner_pressure",
                value=owner,
                relation="has_owner_pressure",
            )
        _add_edge(
            anchors_by_id,
            edges,
            source=signature_anchor,
            kind="wrapper_family",
            value=signature.wrapper_family_hint,
            relation="has_wrapper_family",
        )
    for event in report.action_events:
        event_anchor = _anchor_id("action_event", event.event_id)
        anchors_by_id[event_anchor] = {"id": event_anchor, "kind": "action_event", "ref": event.event_id}
        if event.action_signature_ref:
            _add_edge(
                anchors_by_id,
                edges,
                source=event_anchor,
                kind="action_signature",
                value=event.action_signature_ref,
                relation="has_action_signature",
            )
        for candidate_id in event.candidate_ids:
            _add_edge(
                anchors_by_id,
                edges,
                source=event_anchor,
                kind="candidate",
                value=candidate_id,
                relation="has_candidate",
            )
    for cluster in report.repetition_clusters:
        cluster_anchor = _anchor_id("repetition_cluster", cluster.cluster_id)
        anchors_by_id[cluster_anchor] = {
            "id": cluster_anchor,
            "kind": "repetition_cluster",
            "ref": cluster.cluster_id,
        }
        _add_edge(
            anchors_by_id,
            edges,
            source=cluster_anchor,
            kind="action_signature",
            value=cluster.signature_id,
            relation="has_action_signature",
        )
        if cluster.wrapper_gap is not None:
            _add_edge(
                anchors_by_id,
                edges,
                source=cluster_anchor,
                kind="wrapper_gap",
                value=cluster.wrapper_gap.candidate_id,
                relation="has_wrapper_gap",
            )
    for gap in report.wrapper_gap_candidates:
        gap_anchor = _anchor_id("wrapper_gap", gap.candidate_id)
        anchors_by_id[gap_anchor] = {"id": gap_anchor, "kind": "wrapper_gap", "ref": gap.candidate_id}
        _add_edge(
            anchors_by_id,
            edges,
            source=gap_anchor,
            kind="action_signature",
            value=gap.signature_id,
            relation="has_action_signature",
        )
    anchors = sorted(anchors_by_id.values(), key=lambda item: (item["kind"], item["id"]))
    return anchors, sorted(edges, key=lambda item: (item["source"], item["relation"], item["target"]))


def _add_edge(
    anchors_by_id: dict[str, dict[str, str]],
    edges: list[dict[str, str]],
    *,
    source: str,
    kind: str,
    value: str,
    relation: str,
) -> None:
    target = _anchor_id(kind, value)
    anchors_by_id[target] = {"id": target, "kind": kind, "ref": value}
    edges.append({"source": source, "target": target, "relation": relation})


def _anchor_id(kind: str, value: str) -> str:
    return f"{kind}:{safe_checkpoint_name(value).lower()[:96] or 'unknown'}"
