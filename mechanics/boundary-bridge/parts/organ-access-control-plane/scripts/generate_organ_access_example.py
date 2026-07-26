#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))

from aoa_sdk.contracts.organs import OrganRegistrySource  # noqa: E402
from aoa_sdk.organs.registry import compile_registry  # noqa: E402

OBSERVED_AT = "2026-07-25T12:00:00Z"
EXPIRES_AT = "2027-01-01T00:00:00Z"
DIGESTS = {
    "aoa-kag": "sha256:" + "a" * 64,
    "aoa-stats": "sha256:" + "b" * 64,
    "aoa-decisions": "sha256:" + "c" * 64,
}
ORGANS = (
    (
        "aoa-kag",
        "Owner-qualified knowledge retrieval with source-preserving handoff.",
        "knowledge-retrieval",
        "retrieve-knowledge",
        ("knowledge", "provenance", "relations"),
    ),
    (
        "aoa-stats",
        "Owner-qualified operational measurement and bounded summaries.",
        "measurement-read",
        "inspect-measurement",
        ("metrics", "measurement", "coverage"),
    ),
    (
        "aoa-decisions",
        "Owner-qualified durable decision lookup and rationale retrieval.",
        "decision-retrieval",
        "retrieve-decision",
        ("decision", "rationale", "history"),
    ),
)


def evidence(organ_id: str) -> dict:
    return {
        "owner": organ_id,
        "evidence_ref": f"owner://{organ_id}/decision/shadow-review",
        "revision": "example-shadow-v1",
        "observed_at": OBSERVED_AT,
        "expires_at": EXPIRES_AT,
    }


def maturity(organ_id: str) -> dict:
    names = (
        "declared",
        "owner_reviewed",
        "packaged",
        "exported",
        "deployed",
        "process_alive",
        "endpoint_ready",
        "registry_indexed",
        "consumer_registered",
        "schema_observed",
        "call_succeeded",
        "result_grounded",
        "freshness_satisfied",
        "owner_accepted",
        "cross_organ_proven",
        "rollback_proven",
    )
    return {
        name: (
            {
                "state": "asserted",
                "evidence": evidence(organ_id),
                "freshness_policy": "example-owner-review-v1",
            }
            if name == "declared"
            else {"state": "not_asserted"}
        )
        for name in names
    }


def record(
    organ_id: str,
    description: str,
    capability_id: str,
    primitive_id: str,
    terms: tuple[str, ...],
) -> dict:
    contour = organ_id.removeprefix("aoa-") + "-read"
    return {
        "organ_id": organ_id,
        "display_name": organ_id,
        "description": description,
        "owners": {
            "source_owner": organ_id,
            "access_owner": organ_id,
            "runtime_owner": "abyss-stack",
            "proof_owner": "aoa-evals",
            "acceptance_owner": organ_id,
        },
        "registry_state": "shadow",
        "authority_ceiling": "read",
        "authentication_requirements": ["owner-bearer"],
        "credential_contours": {"read": contour},
        "revisions": {
            "source": {
                "revision": "example-shadow-v1",
                "digest": DIGESTS[organ_id],
            }
        },
        "freshness_policy": {
            "policy_id": f"{organ_id.removeprefix('aoa-')}-owner-freshness",
            "max_age_seconds": 300,
            "stale_readable_seconds": 0,
            "cache_scope": "task",
            "provider_watermark_required": True,
        },
        "freshness_state": "unknown",
        "eval_refs": ["eval://aoa-organ-access-admission-integrity"],
        "eval_status": "candidate",
        "capabilities": [
            {
                "capability_id": capability_id,
                "summary": description,
                "policy_family": "read",
                "credential_class": contour,
                "primitives": [
                    {
                        "primitive_id": primitive_id,
                        "kind": "tool",
                        "effect_class": "observe",
                        "policy_family": "read",
                        "input_schema_ref": f"owner://{organ_id}/schema/input",
                        "output_schema_ref": f"owner://{organ_id}/schema/output",
                        "approval_required": False,
                        "idempotency": "read_only",
                        "maximum_blast_radius": "read-only owner response",
                    }
                ],
                "task_intent_terms": list(terms),
                "owner_payload_schema_ref": f"owner://{organ_id}/schema/payload",
                "eval_refs": ["eval://aoa-organ-access-admission-integrity"],
            }
        ],
        "maturity": maturity(organ_id),
        "rollback_route": f"owner://{organ_id}/rollback/shadow",
        "support_route": f"owner://{organ_id}/support",
        "handoff": {
            "input_ref_kind": "task-intent-ref",
            "output_ref_kind": "owner-result-ref",
            "next_owner": "requesting-consumer",
            "stop_states": ["owner-review-required", "freshness-blocked"],
        },
    }


def rendered_payloads() -> dict[Path, str]:
    source = OrganRegistrySource.model_validate(
        {
            "registry_id": "abyss-wave1-example",
            "workspace_owner": "os-abyss",
            "authored_at": OBSERVED_AT,
            "expires_at": EXPIRES_AT,
            "owner_decision_refs": [
                "decision://AOA-SDK-D-0075",
                "decision://ABYSS-STACK-D-0087",
            ],
            "records": [record(*item) for item in ORGANS],
        }
    )
    projection = compile_registry(source)
    return {
        REPO_ROOT
        / "mechanics"
        / "boundary-bridge"
        / "parts"
        / "organ-access-control-plane"
        / "examples"
        / "organ_registry.wave1-shadow.example.json": (
            json.dumps(
                source.model_dump(mode="json"),
                indent=2,
                ensure_ascii=True,
                sort_keys=True,
            )
            + "\n"
        ),
        REPO_ROOT
        / "mechanics"
        / "boundary-bridge"
        / "parts"
        / "organ-access-control-plane"
        / "examples"
        / "organ_registry.wave1-shadow.projection.json": (
            json.dumps(
                projection.model_dump(mode="json"),
                indent=2,
                ensure_ascii=True,
                sort_keys=True,
            )
            + "\n"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale: list[str] = []
    for path, rendered in rendered_payloads().items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
                stale.append(str(path.relative_to(REPO_ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
    if stale:
        print("stale organ access examples:")
        for path in stale:
            print(f"  - {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
