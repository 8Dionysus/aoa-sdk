from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
EVIDENCE_PATH = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "consumed-surface-posture-gate"
    / "evidence"
    / "routing-succession-r0-baseline.json"
)


def load_evidence() -> dict[str, object]:
    return json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))


def test_routing_succession_baseline_is_pinned_and_non_authoritative() -> None:
    evidence = load_evidence()

    assert evidence["schema_version"] == "aoa_sdk_routing_succession_r0_baseline_v1"
    assert evidence["scope"]["stage"] == "R0 read-only baseline"
    assert "does not switch routing authority" in evidence["scope"]["authority_posture"]
    assert (
        evidence["primary_baseline"]["aoa-routing"]["origin_main"]
        == "cde31e568e49c5a50afbd89071cf72abd9733d99"
    )
    assert (
        evidence["primary_baseline"]["aoa-sdk"]["origin_main"]
        == "cdd3af4e1a7d0f0ffc514b65d6dee3b5b838a530"
    )


def test_routing_succession_baseline_covers_producers_consumers_and_dispositions() -> None:
    evidence = load_evidence()
    producer_graph = evidence["producer_graph"]

    assert producer_graph["canonical_owner_count"] == 1
    assert producer_graph["canonical_owner"] == "aoa-routing"
    assert producer_graph["input_repository_count"] == len(
        producer_graph["input_repositories"]
    )
    assert producer_graph["root_output_count"] == 14
    assert len(producer_graph["root_outputs"]) == 14
    assert all(item["producer"] for item in producer_graph["root_outputs"])
    assert all(item["disposition"] for item in producer_graph["root_outputs"])
    assert len(evidence["consumer_registry"]) >= 16

    required_dispositions = {
        "absorb",
        "merge",
        "preserve",
        "retire",
        "archive",
        "external",
    }
    observed = {
        token
        for row in evidence["surface_disposition"]
        for token in row["disposition"].replace(" and ", " ").split()
    }
    assert required_dispositions <= observed


def test_routing_succession_baseline_keeps_false_green_and_trust_denial_visible() -> None:
    evidence = load_evidence()
    runtime = evidence["runtime_loading_map"]
    trust = evidence["artifact_baseline"]["trust_registry"]

    assert runtime["health_endpoint"]["verdict"] == "false green"
    assert runtime["sync_check"]["ok"] is False
    assert runtime["root_outputs_stale_against_origin_main"] == 8
    assert runtime["root_outputs_missing_from_runtime_mirror"] == 4
    assert trust["exact_origin_main_admission"] == {
        "expected_source_ref": "cde31e568e49c5a50afbd89071cf72abd9733d99",
        "ok": False,
        "verdict": "deny",
        "reason": "source_ref_mismatch",
    }


def test_routing_succession_g0_has_no_unclassified_dependency() -> None:
    evidence = load_evidence()
    gate = evidence["gate_g0"]

    assert evidence["unknown_dependencies"] == []
    assert gate["verdict"] == "pass"
    assert all(
        gate[key] is True
        for key in (
            "all_active_organization_repositories_scanned",
            "all_active_consumers_registered",
            "all_root_generated_artifacts_have_producers",
            "all_other_generated_or_generated_named_surfaces_have_producer_classification",
            "all_top_level_and_mechanic_surface_families_have_dispositions",
            "runtime_path_reproduced",
            "cost_hypothesis_has_measurable_baseline",
            "unknown_dependencies_empty",
        )
    )
    assert len(evidence["required_compatibility_fixtures"]) >= 18
