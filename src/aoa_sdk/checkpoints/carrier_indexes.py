"""Generated checkpoint carrier-candidate navigation indexes."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..models import CarrierCandidate, CarrierIntelligenceReport
from ..workspace.discovery import Workspace


def checkpoint_carrier_candidate_intelligence_index_path(workspace: Workspace) -> Path:
    return (
        workspace.repo_path("aoa-sdk")
        / ".aoa"
        / "session-growth"
        / "indexes"
        / "checkpoint-carrier-candidate-intelligence.min.json"
    )


def build_checkpoint_carrier_candidate_intelligence_index(
    report: CarrierIntelligenceReport,
) -> dict[str, Any]:
    candidates = sorted(report.carrier_candidates, key=lambda item: item.candidate_id)
    anchors, edges = _graph_ready(candidates)
    return {
        "schema_version": 1,
        "artifact_type": "checkpoint_carrier_candidate_intelligence_navigation_index_v1",
        "boundary_note": (
            "Generated navigation only; carrier candidates are ecosystem route "
            "evidence, not accepted mechanics, installed tools, registered MCP "
            "services, hooks, automation, owner verdicts, memory, proof, RAG, "
            "or GraphRAG authority."
        ),
        "repo_label": report.repo_label,
        "counts": {
            "carrier_candidates": len(candidates),
            "sample_audit": len(report.sample_audit),
            "by_carrier_kind": dict(
                sorted(Counter(candidate.carrier_kind for candidate in candidates).items())
            ),
            "by_owner_scope": dict(
                sorted(Counter(candidate.owner_scope for candidate in candidates).items())
            ),
            "by_execution_risk": dict(
                sorted(Counter(candidate.execution_risk for candidate in candidates).items())
            ),
            "by_installability": dict(
                sorted(Counter(candidate.installability for candidate in candidates).items())
            ),
            "by_existing_fit": dict(
                sorted(
                    Counter(
                        candidate.existing_carrier_fit.fit_status
                        for candidate in candidates
                    ).items()
                )
            ),
            "by_cross_repo_pressure": dict(
                sorted(
                    Counter(str(candidate.cross_repo_pressure).lower() for candidate in candidates).items()
                )
            ),
            "graph_anchors": len(anchors),
            "graph_edges": len(edges),
        },
        "carrier_candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "signature_id": candidate.signature_id,
                "carrier_kind": candidate.carrier_kind,
                "owner_scope": candidate.owner_scope,
                "source_wrapper_family": candidate.source_wrapper_family,
                "action": candidate.action,
                "object": candidate.object,
                "cross_repo_pressure": candidate.cross_repo_pressure,
                "execution_risk": candidate.execution_risk,
                "execution_posture": candidate.execution_posture,
                "installability": candidate.installability,
                "draftability": candidate.carrier_readiness.draftability,
                "existing_fit": candidate.existing_carrier_fit.fit_status,
                "evidence_refs": candidate.evidence_refs,
                "stop_lines": candidate.stop_lines,
            }
            for candidate in candidates
        ],
        "by_carrier_kind": _group_candidates(candidates, "carrier_kind"),
        "by_owner_scope": _group_candidates(candidates, "owner_scope"),
        "by_execution_risk": _group_candidates(candidates, "execution_risk"),
        "by_installability": _group_candidates(candidates, "installability"),
        "by_existing_fit": _by_existing_fit(candidates),
        "by_cross_repo_pressure": _by_cross_repo_pressure(candidates),
        "by_source_wrapper_family": _group_candidates(candidates, "source_wrapper_family"),
        "sample_audit": [sample.model_dump(mode="json") for sample in report.sample_audit],
        "graph_ready": {
            "anchors": anchors,
            "edges": edges,
        },
    }


def write_checkpoint_carrier_candidate_intelligence_index(
    *,
    workspace: Workspace,
    report: CarrierIntelligenceReport,
) -> Path:
    path = checkpoint_carrier_candidate_intelligence_index_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            build_checkpoint_carrier_candidate_intelligence_index(report),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _group_candidates(candidates: list[CarrierCandidate], attr: str) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for candidate in candidates:
        grouped[str(getattr(candidate, attr))].append(candidate.candidate_id)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _by_existing_fit(candidates: list[CarrierCandidate]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.existing_carrier_fit.fit_status].append(candidate.candidate_id)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _by_cross_repo_pressure(candidates: list[CarrierCandidate]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for candidate in candidates:
        grouped[str(candidate.cross_repo_pressure).lower()].append(candidate.candidate_id)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _graph_ready(
    candidates: list[CarrierCandidate],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    anchors_by_id: dict[str, dict[str, str]] = {}
    edges: list[dict[str, str]] = []
    for candidate in candidates:
        candidate_anchor = _anchor_id("carrier_candidate", candidate.candidate_id)
        anchors_by_id[candidate_anchor] = {
            "id": candidate_anchor,
            "kind": "carrier_candidate",
            "ref": candidate.candidate_id,
        }
        for kind, value, relation in (
            ("action_signature", candidate.signature_id, "has_action_signature"),
            ("carrier_kind", candidate.carrier_kind, "has_carrier_kind"),
            ("owner_scope", candidate.owner_scope, "has_owner_scope"),
            ("execution_risk", candidate.execution_risk, "has_execution_risk"),
            ("installability", candidate.installability, "has_installability"),
            ("source_wrapper_family", candidate.source_wrapper_family, "has_source_wrapper_family"),
        ):
            _add_edge(
                anchors_by_id,
                edges,
                source=candidate_anchor,
                kind=kind,
                value=value,
                relation=relation,
            )
        for owner in candidate.owner_pressure:
            _add_edge(
                anchors_by_id,
                edges,
                source=candidate_anchor,
                kind="owner_pressure",
                value=owner,
                relation="has_owner_pressure",
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
    anchors_by_id.setdefault(target, {"id": target, "kind": kind, "ref": value})
    edges.append({"source": source, "target": target, "relation": relation})


def _anchor_id(kind: str, value: str) -> str:
    return f"{kind}:{value}"
