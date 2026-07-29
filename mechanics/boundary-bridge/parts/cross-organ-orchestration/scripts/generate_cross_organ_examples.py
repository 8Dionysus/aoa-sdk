#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[5]
SRC_ROOT = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aoa_sdk.contracts.control_plane import canonical_digest  # noqa: E402
from aoa_sdk.contracts.organ_orchestration import (  # noqa: E402
    CrossOrganOrchestrationRequest,
    CrossOrganStageObservation,
    HostVisibleStageReceipt,
    OrchestrationOwners,
    SchemaIdentity,
    StageSchemaContract,
    TypedArtifactRef,
)
from aoa_sdk.organs.orchestration import (  # noqa: E402
    advance_orchestration,
    start_orchestration,
    validate_orchestration_run,
)
from aoa_sdk.organs.registry import sha256_digest  # noqa: E402


NOW = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
ZERO_DIGEST = "sha256:" + ("0" * 64)
HOST_ID = "abyss-stack-example"
OWNER_REVISIONS = {
    "aoa-kag": "58ab52ffc06bab5cc28842a0b4336c6efa16b6ff",
    "aoa-memo": "e0d3653c11d948f962bcb033749c86c52388ec5f",
    "aoa-evals": "4d03125d0961dbc0b15332f1a146cd0f7f08eb23",
}


def _schema(
    owner: str,
    ref: str,
    digest: str,
    version: str,
) -> SchemaIdentity:
    return SchemaIdentity(
        owner=owner,
        schema_ref=ref,
        schema_digest=f"sha256:{digest}",
        source_revision=OWNER_REVISIONS[owner],
        schema_version=version,
    )


SCHEMAS = {
    "kag_evidence": _schema(
        "aoa-kag",
        "schemas/kag-mcp-result.schema.json",
        "1516bc25755b26c156a58709c5e7600e276daa21f115d7cdc61031cbd67162d5",
        "aoa_kag_mcp_result_v1",
    ),
    "memo_candidate": _schema(
        "aoa-memo",
        "schemas/memory-ports/local_memo_candidate.schema.json",
        "6a33ac41ac90d4af29827a637b8f3cea24ecb45ca259d866e79000a2a784c0d9",
        "aoa_local_memo_candidate_v1",
    ),
    "eval_request": _schema(
        "aoa-evals",
        "mechanics/proof-object/parts/eval-authoring/schemas/eval-need.schema.json",
        "751dd78f0280dc2cd089e30b3a7275182656e8350cf84c458f98734d16b4fad1",
        "eval_need_v1",
    ),
    "eval_result": _schema(
        "aoa-evals",
        "mechanics/publication-receipts/parts/receipt-payload/schemas/"
        "eval-result-receipt.schema.json",
        "786c3bd7902fe78224adfc5ac76ed7a43b49f78bb6a5ade140a416458339a82a",
        "aoa_eval_result_receipt_v1",
    ),
    "owner_acceptance": _schema(
        "aoa-memo",
        "schemas/support-objects/reviewed_intake_landing_receipt.schema.json",
        "e3a1e93846340f4d850028eeb722a32458cff6527fe38a6366052edf86a1239f",
        "aoa_memo_reviewed_intake_landing_receipt_v1",
    ),
}


def _request() -> CrossOrganOrchestrationRequest:
    root_schema = SchemaIdentity(
        owner="abyss-stack",
        schema_ref="urn:abyss-stack:cross-organ-intent:v1",
        schema_digest=sha256_digest({"fixture": "cross-organ-intent-v1"}),
        source_revision="example-host-revision",
        schema_version="abyss_stack_cross_organ_intent_v1",
    )
    root_input = TypedArtifactRef(
        ref_kind="orchestration_intent",
        owner="abyss-stack",
        artifact_ref="example://orchestration/intent/research-1",
        artifact_digest=sha256_digest(
            {"intent": "demonstrate an explicit cross-organ chain"}
        ),
        source_revision="example-host-revision",
        schema_identity=root_schema,
        authority_ceiling="read",
        created_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=1),
    )
    contracts = (
        StageSchemaContract(
            stage_kind="kag_evidence",
            owner="aoa-kag",
            input_ref_kind="orchestration_intent",
            output_ref_kind="kag_evidence",
            output_schema=SCHEMAS["kag_evidence"],
            authority_ceiling="read",
            effect_class="observe",
            next_owner="aoa-memo",
        ),
        StageSchemaContract(
            stage_kind="memo_candidate",
            owner="aoa-memo",
            input_ref_kind="kag_evidence",
            output_ref_kind="memo_candidate",
            output_schema=SCHEMAS["memo_candidate"],
            authority_ceiling="candidate",
            effect_class="prepare_candidate",
            next_owner="aoa-evals",
        ),
        StageSchemaContract(
            stage_kind="eval_request",
            owner="aoa-evals",
            input_ref_kind="memo_candidate",
            output_ref_kind="eval_request",
            output_schema=SCHEMAS["eval_request"],
            authority_ceiling="candidate",
            effect_class="prepare_candidate",
            next_owner="aoa-evals",
        ),
        StageSchemaContract(
            stage_kind="eval_result",
            owner="aoa-evals",
            input_ref_kind="eval_request",
            output_ref_kind="eval_result",
            output_schema=SCHEMAS["eval_result"],
            authority_ceiling="read",
            effect_class="validate",
            next_owner="aoa-memo",
        ),
        StageSchemaContract(
            stage_kind="owner_acceptance",
            owner="aoa-memo",
            input_ref_kind="eval_result",
            output_ref_kind="owner_acceptance",
            output_schema=SCHEMAS["owner_acceptance"],
            authority_ceiling="internal_effect",
            effect_class="accept_source",
            next_owner=None,
        ),
    )
    return CrossOrganOrchestrationRequest(
        request_id="cross-organ-research-1",
        intent=(
            "Demonstrate the typed KAG evidence to reviewed owner acceptance "
            "boundary without executing owner tools."
        ),
        requested_by="public-safe-fixture",
        host_id=HOST_ID,
        owners=OrchestrationOwners(
            evidence_owner="aoa-kag",
            memory_owner="aoa-memo",
            proof_owner="aoa-evals",
            acceptance_owner="aoa-memo",
            runtime_owner="abyss-stack",
        ),
        root_input=root_input,
        stage_contracts=contracts,
        evidence_refs=(
            _evidence(
                "aoa-sdk",
                "example://decision/AOA-SDK-D-0080",
                "example-sdk-revision",
                NOW,
            ),
        ),
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )


def _evidence(
    owner: str,
    ref: str,
    revision: str,
    observed_at: datetime,
) -> dict[str, Any]:
    return {
        "owner": owner,
        "evidence_ref": ref,
        "revision": revision,
        "observed_at": observed_at.isoformat(),
        "expires_at": (NOW + timedelta(hours=1)).isoformat(),
    }


def _output(
    stage_kind: str,
    *,
    at: datetime,
) -> TypedArtifactRef:
    schema = SCHEMAS[stage_kind]
    return TypedArtifactRef(
        ref_kind=stage_kind,
        owner=schema.owner,
        artifact_ref=f"example://{schema.owner}/{stage_kind}/1",
        artifact_digest=sha256_digest(
            {
                "fixture": True,
                "stage_kind": stage_kind,
                "owner": schema.owner,
                "schema_digest": schema.schema_digest,
            }
        ),
        source_revision=schema.source_revision,
        schema_identity=schema,
        authority_ceiling=(
            "candidate"
            if stage_kind in {"memo_candidate", "eval_request"}
            else "internal_effect"
            if stage_kind == "owner_acceptance"
            else "read"
        ),
        created_at=at,
        expires_at=NOW + timedelta(hours=1),
    )


def _observation(
    run: Any,
    *,
    sequence: int,
    freshness_state: str = "exact",
    transition_state: str | None = None,
) -> CrossOrganStageObservation:
    contract = run.request.stage_contracts[sequence]
    at = NOW + timedelta(minutes=(sequence + 1) * 5)
    input_ref = (
        run.request.root_input
        if not run.stages
        else run.stages[-1].observation.output_ref
    )
    output_ref = _output(contract.output_ref_kind, at=at)
    transition = transition_state or (
        "accepted_terminal" if sequence == 4 else "proceed"
    )
    outcome = {
        "kag_evidence": "observed",
        "memo_candidate": "candidate_created",
        "eval_request": "request_created",
        "eval_result": "validated",
        "owner_acceptance": "accepted",
    }[contract.stage_kind]
    if transition == "stopped":
        outcome = "stopped"
    receipt = HostVisibleStageReceipt(
        receipt_id=f"host-receipt-{sequence + 1}",
        receipt_ref=f"example://abyss-stack/receipt/{sequence + 1}",
        receipt_digest=ZERO_DIGEST,
        host_id=HOST_ID,
        run_id=run.run_id,
        stage_kind=contract.stage_kind,
        previous_snapshot_digest=run.snapshot_digest,
        input_artifact_digest=input_ref.artifact_digest,
        output_artifact_digest=output_ref.artifact_digest,
        issued_at=at + timedelta(seconds=30),
        outcome=outcome,
        owner_receipt_refs=(
            (output_ref,) if contract.stage_kind == "owner_acceptance" else ()
        ),
    )
    receipt = receipt.model_copy(
        update={
            "receipt_digest": canonical_digest(
                receipt,
                exclude={"receipt_digest"},
            )
        }
    )
    is_acceptance = contract.stage_kind == "owner_acceptance"
    return CrossOrganStageObservation.model_validate(
        {
            "stage_kind": contract.stage_kind,
            "stage_owner": contract.owner,
            "source_revision": contract.output_schema.source_revision,
            "input_ref": input_ref.model_dump(mode="json"),
            "output_ref": output_ref.model_dump(mode="json"),
            "input_schema_identity": input_ref.schema_identity.model_dump(
                mode="json"
            ),
            "output_schema_identity": contract.output_schema.model_dump(
                mode="json"
            ),
            "evidence_refs": [
                _evidence(
                    contract.owner,
                    f"example://{contract.owner}/evidence/{sequence + 1}",
                    contract.output_schema.source_revision,
                    at,
                )
            ],
            "freshness_state": freshness_state,
            "observed_at": at.isoformat(),
            "expires_at": (NOW + timedelta(hours=1)).isoformat(),
            "authority_ceiling": contract.authority_ceiling,
            "effect_class": contract.effect_class,
            "applied_state": (
                "applied"
                if is_acceptance
                else "candidate_only"
                if contract.effect_class == "prepare_candidate"
                else "not_applied"
            ),
            "receipt": receipt.model_dump(mode="json"),
            "next_owner": (
                contract.next_owner if transition == "proceed" else None
            ),
            "transition_state": transition,
            "stop_reason_codes": (
                ["stale_owner_evidence"] if transition == "stopped" else []
            ),
            "review_ref": (
                _evidence(
                    contract.owner,
                    "example://aoa-memo/review/acceptance-1",
                    contract.output_schema.source_revision,
                    at,
                )
                if is_acceptance
                else None
            ),
            "acceptance_decision": "accepted" if is_acceptance else None,
        }
    )


def render_outputs() -> dict[str, str]:
    request = _request()
    accepted = start_orchestration(request)
    for sequence in range(5):
        accepted = advance_orchestration(
            accepted,
            _observation(accepted, sequence=sequence),
        )
    validate_orchestration_run(accepted)

    stopped = start_orchestration(request)
    stopped = advance_orchestration(
        stopped,
        _observation(
            stopped,
            sequence=0,
            freshness_state="stale_readable",
            transition_state="stopped",
        ),
    )
    validate_orchestration_run(stopped)

    values = {
        "cross-organ.request.example.json": request,
        "cross-organ.accepted-shape.example.json": accepted,
        "cross-organ.stale-stop.example.json": stopped,
    }
    return {
        name: json.dumps(
            value.model_dump(mode="json"),
            indent=2,
            ensure_ascii=True,
            sort_keys=True,
        )
        + "\n"
        for name, value in values.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output_dir = Path(__file__).resolve().parents[1] / "examples"
    if not args.check:
        output_dir.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for filename, rendered in render_outputs().items():
        destination = output_dir / filename
        if args.check:
            if (
                not destination.is_file()
                or destination.read_text(encoding="utf-8") != rendered
            ):
                stale.append(str(destination.relative_to(REPO_ROOT)))
        else:
            destination.write_text(rendered, encoding="utf-8")
    if stale:
        print("stale cross-organ orchestration examples:")
        for path in stale:
            print(f"  - {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
