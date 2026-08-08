#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aoa_sdk.contracts.organs import (  # noqa: E402
    ActivationRequest,
    CompatibilityObservation,
    OrganActivationPlan,
    OrganRecord,
    OrganRegistryProjection,
    OrganRegistrySource,
    OwnerResultReviewReceipt,
    OrganResultEnvelope,
    OrganResultMetadata,
)
from aoa_sdk.contracts.organ_admission import (  # noqa: E402
    AdmissionDecisionReceipt,
    AdmissionEvidenceReceipt,
    OrganAdmissionAuthorization,
    OrganAdmissionBaselineAudit,
    OrganAdmissionCandidate,
    OrganAdmissionRequest,
    OrganAdmissionRun,
)
from aoa_sdk.contracts.organ_registry_v2 import (  # noqa: E402
    OrganContourSupplement,
    OrganContourRecord,
    OrganRegistryProjectionV2,
    OrganRegistryRuntimeOverlay,
    OrganRegistrySourceV2,
)
from aoa_sdk.contracts.admission_keeper import (  # noqa: E402
    AdmissionKeeperCycle,
    AdmissionEvidenceNode,
    AdmissionKeeperRefreshPlan,
    AdmissionKeeperSpec,
    AdmissionKeeperState,
)
from aoa_sdk.contracts.tasks import OwnerTaskRecord, TaskAuditReceipt  # noqa: E402


OUTPUTS = {
    "organ-contract.schema.json": OrganRecord,
    "organ-registry-source.schema.json": OrganRegistrySource,
    "organ-registry-projection.schema.json": OrganRegistryProjection,
    "organ-activation-request.schema.json": ActivationRequest,
    "organ-activation-plan.schema.json": OrganActivationPlan,
    "organ-compatibility-observation.schema.json": CompatibilityObservation,
    "organ-result-metadata.schema.json": OrganResultMetadata,
    "organ-result-envelope.schema.json": OrganResultEnvelope,
    "organ-owner-result-review.schema.json": OwnerResultReviewReceipt,
    "organ-admission-request.schema.json": OrganAdmissionRequest,
    "organ-admission-evidence.schema.json": AdmissionEvidenceReceipt,
    "organ-admission-run.schema.json": OrganAdmissionRun,
    "organ-admission-candidate.schema.json": OrganAdmissionCandidate,
    "organ-admission-decision.schema.json": AdmissionDecisionReceipt,
    "organ-admission-authorization.schema.json": OrganAdmissionAuthorization,
    "organ-admission-baseline-audit.schema.json": OrganAdmissionBaselineAudit,
    "organ-contour-v2.schema.json": OrganContourRecord,
    "organ-contour-supplement.schema.json": OrganContourSupplement,
    "organ-registry-source-v2.schema.json": OrganRegistrySourceV2,
    "organ-registry-projection-v2.schema.json": OrganRegistryProjectionV2,
    "organ-registry-runtime-overlay.schema.json": OrganRegistryRuntimeOverlay,
    "organ-admission-keeper-spec.schema.json": AdmissionKeeperSpec,
    "organ-admission-keeper-node.schema.json": AdmissionEvidenceNode,
    "organ-admission-keeper-state.schema.json": AdmissionKeeperState,
    "organ-admission-keeper-plan.schema.json": AdmissionKeeperRefreshPlan,
    "organ-admission-keeper-cycle.schema.json": AdmissionKeeperCycle,
    "owner-task-record.schema.json": OwnerTaskRecord,
    "owner-task-audit.schema.json": TaskAuditReceipt,
}

PART_LOCAL_OUTPUTS = {
    "organ-contour-v2.schema.json",
    "organ-contour-supplement.schema.json",
    "organ-registry-source-v2.schema.json",
    "organ-registry-projection-v2.schema.json",
    "organ-registry-runtime-overlay.schema.json",
    "organ-admission-keeper-spec.schema.json",
    "organ-admission-keeper-node.schema.json",
    "organ-admission-keeper-state.schema.json",
    "organ-admission-keeper-plan.schema.json",
    "organ-admission-keeper-cycle.schema.json",
    "owner-task-record.schema.json",
    "owner-task-audit.schema.json",
}


def render(filename: str, model: type) -> str:
    schema = model.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"urn:aoa-sdk:organ-access:{filename}"
    return (
        json.dumps(
            schema,
            indent=2,
            ensure_ascii=True,
            sort_keys=True,
        )
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    legacy_output_dir = REPO_ROOT / "schemas" / "organ-access"
    part_output_dir = PART_ROOT / "schemas"
    if not args.check:
        legacy_output_dir.mkdir(parents=True, exist_ok=True)
        part_output_dir.mkdir(parents=True, exist_ok=True)

    stale: list[str] = []
    for filename, model in OUTPUTS.items():
        output_dir = (
            part_output_dir if filename in PART_LOCAL_OUTPUTS else legacy_output_dir
        )
        destination = output_dir / filename
        expected = render(filename, model)
        if args.check:
            if not destination.is_file() or destination.read_text(encoding="utf-8") != expected:
                stale.append(str(destination.relative_to(REPO_ROOT)))
        else:
            destination.write_text(expected, encoding="utf-8")
    for filename in sorted(PART_LOCAL_OUTPUTS):
        retired = legacy_output_dir / filename
        if retired.exists() or retired.is_symlink():
            stale.append(
                f"{retired.relative_to(REPO_ROOT)} (retired competing location)"
            )
    if stale:
        print("stale organ access schemas:")
        for path in stale:
            print(f"  - {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
