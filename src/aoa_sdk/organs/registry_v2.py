"""Deterministic contour-addressed organ registry compilation and migration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from ..contracts.organ_registry_v2 import (
    ContourRuntimeIdentity,
    OrganContourSupplement,
    OrganContourProjectionEntry,
    OrganContourRecord,
    OrganRecordV2,
    OrganRegistryProjectionV2,
    OrganRegistryRuntimeOverlay,
    OrganRegistrySourceV2,
)
from ..contracts.organs import (
    CapabilityContract,
    NON_DISCOVERABLE_STATES,
    MaturityEvidence,
    OrganMaturityVector,
    OrganRevisions,
    OrganRecord,
    OrganRegistrySource,
    PolicyFamily,
    QualifiedEvidenceRef,
)
from .registry import (
    OrganRegistryError,
    canonical_json_bytes,
    load_registry_source,
    reject_secret_material,
    sha256_digest,
)


def load_registry_source_v2(path: str | Path) -> OrganRegistrySourceV2:
    resolved = Path(path).expanduser().resolve(strict=False)
    if not resolved.is_file() or resolved.is_symlink():
        raise OrganRegistryError(
            f"explicit v2 registry must be a regular non-symlink file: {resolved}"
        )
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
        reject_secret_material(payload)
        return OrganRegistrySourceV2.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise OrganRegistryError(f"invalid v2 organ registry {resolved}: {exc}") from exc


def migrate_registry_v1_to_v2(
    source: OrganRegistrySource,
    *,
    migration_decision_ref: str,
) -> OrganRegistrySourceV2:
    """Map each v1 policy/credential group to one independent v2 contour.

    The migration preserves every v1 claim byte-for-byte where possible.  It
    deliberately does not upgrade a state, refresh an expiry, invent a proof,
    or fabricate a last-good target.
    """

    records = tuple(_migrate_record(record) for record in source.records)
    decision_refs = tuple(
        dict.fromkeys((*source.owner_decision_refs, migration_decision_ref))
    )
    return OrganRegistrySourceV2(
        registry_id=source.registry_id,
        workspace_owner=source.workspace_owner,
        authored_at=source.authored_at,
        expires_at=source.expires_at,
        owner_decision_refs=decision_refs,
        records=records,
    )


def migrate_registry_file_v1_to_v2(
    path: str | Path,
    *,
    migration_decision_ref: str,
) -> OrganRegistrySourceV2:
    return migrate_registry_v1_to_v2(
        load_registry_source(path),
        migration_decision_ref=migration_decision_ref,
    )


def apply_registry_runtime_overlay(
    source: OrganRegistrySourceV2,
    overlay: OrganRegistryRuntimeOverlay,
) -> OrganRegistrySourceV2:
    """Apply exact runtime bindings without changing authority or evidence claims."""

    entries = {(item.organ_id, item.contour_id): item for item in overlay.contours}
    known = {
        (record.organ_id, contour.contour_id)
        for record in source.records
        for contour in record.contours
    }
    unknown = sorted(set(entries) - known)
    if unknown:
        raise OrganRegistryError(f"runtime overlay has unknown contours: {unknown!r}")
    records: list[OrganRecordV2] = []
    for record in source.records:
        contours: list[OrganContourRecord] = []
        for contour in record.contours:
            replacement = entries.get((record.organ_id, contour.contour_id))
            if replacement is None:
                contours.append(contour)
                continue
            contours.append(
                contour.model_copy(
                    update={
                        "principal_id": replacement.principal_id,
                        "endpoint": replacement.endpoint,
                        "runtime_identity": replacement.runtime_identity,
                        "runtime_identity_evidence": (
                            replacement.runtime_evidence_refs
                        ),
                        "observation_route": replacement.observation_route,
                        "rollback_route": replacement.rollback_route,
                    }
                )
            )
        records.append(record.model_copy(update={"contours": tuple(contours)}))
    decision_refs = tuple(
        dict.fromkeys((*source.owner_decision_refs, overlay.owner_decision_ref))
    )
    return OrganRegistrySourceV2.model_validate(
        source.model_copy(
            update={
                "owner_decision_refs": decision_refs,
                "records": tuple(records),
            }
        ).model_dump(mode="json")
    )


def apply_contour_supplement(
    source: OrganRegistrySourceV2,
    supplement: OrganContourSupplement,
) -> OrganRegistrySourceV2:
    """Add owner-declared contour shapes as unadmitted, unproved shadows."""

    matches = [item for item in source.records if item.organ_id == supplement.organ_id]
    if len(matches) != 1:
        raise OrganRegistryError("contour supplement organ is absent or ambiguous")
    target = matches[0]
    if supplement.source_owner != target.owners.source_owner:
        raise OrganRegistryError("contour supplement source owner is not authoritative")
    existing = {item.contour_id for item in target.contours}
    conflicts = sorted(existing & {item.contour_id for item in supplement.contours})
    if conflicts:
        raise OrganRegistryError(
            f"contour supplement cannot replace existing contours: {conflicts!r}"
        )
    expiry = min(
        source.expires_at,
        supplement.source_evidence.expires_at or source.expires_at,
    )
    unknown = MaturityEvidence(state="not_asserted")
    maturity = OrganMaturityVector(
        **{name: unknown for name in OrganMaturityVector.model_fields}
    )
    additions = tuple(
        OrganContourRecord(
            contour_id=item.contour_id,
            registry_state="shadow",
            authority_class=item.authority_class,
            policy_family=item.policy_family,
            credential_class=item.credential_class,
            principal_id=item.principal_id,
            allowlist=tuple(
                sorted(
                    primitive.mcp_name or primitive.primitive_id
                    for capability in item.capabilities
                    for primitive in capability.primitives
                )
            ),
            capabilities=item.capabilities,
            runtime_identity=ContourRuntimeIdentity(
                source_revision=target.contours[0].runtime_identity.source_revision,
                source_tree_digest=(
                    target.contours[0].runtime_identity.source_tree_digest
                ),
                package_name=f"{target.organ_id}-mcp",
                package_version="unobserved",
            ),
            revisions=OrganRevisions(source=target.contours[0].revisions.source),
            freshness_policy=target.contours[0].freshness_policy,
            maturity=maturity,
            currentness="unknown",
            currentness_expires_at=expiry,
            observation_route=item.observation_route,
            rollback_route=item.rollback_route,
        )
        for item in supplement.contours
    )
    records = tuple(
        record.model_copy(update={"contours": (*record.contours, *additions)})
        if record.organ_id == target.organ_id
        else record
        for record in source.records
    )
    decisions = tuple(
        dict.fromkeys((*source.owner_decision_refs, supplement.owner_decision_ref))
    )
    return OrganRegistrySourceV2.model_validate(
        source.model_copy(
            update={"owner_decision_refs": decisions, "records": records}
        ).model_dump(mode="json")
    )
def compile_registry_v2(
    source: OrganRegistrySourceV2,
    *,
    compiled_at: datetime | None = None,
) -> OrganRegistryProjectionV2:
    timestamp = compiled_at or source.authored_at
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise OrganRegistryError("compiled_at must be timezone-aware")
    timestamp = timestamp.astimezone(timezone.utc)
    if timestamp > source.expires_at:
        raise OrganRegistryError("registry source is expired at compile time")
    payload = source.model_dump(mode="json")
    reject_secret_material(payload)
    source_digest = sha256_digest(payload)
    entries = tuple(
        _project_contour(
            record,
            contour,
            registry_id=source.registry_id,
            source_digest=source_digest,
            compiled_at=timestamp,
            expires_at=source.expires_at,
        )
        for record in sorted(source.records, key=lambda item: item.organ_id)
        for contour in sorted(record.contours, key=lambda item: item.contour_id)
    )
    unsigned = {
        "schema_version": "aoa_organ_registry_projection_v2",
        "registry_id": source.registry_id,
        "workspace_owner": source.workspace_owner,
        "source_digest": source_digest,
        "compiled_at": timestamp.isoformat().replace("+00:00", "Z"),
        "expires_at": source.expires_at.isoformat().replace("+00:00", "Z"),
        "default_admission": "deny",
        "contains_secrets": False,
        "entries": [item.model_dump(mode="json") for item in entries],
    }
    return OrganRegistryProjectionV2.model_validate(
        {**unsigned, "projection_digest": sha256_digest(unsigned)}
    )


def assert_projection_v2_digest(projection: OrganRegistryProjectionV2) -> None:
    payload = projection.model_dump(mode="json")
    claimed = payload.pop("projection_digest")
    actual = sha256_digest(payload)
    if claimed != actual:
        raise OrganRegistryError(
            f"v2 registry projection digest mismatch: expected {claimed}, got {actual}"
        )


def render_registry_source_v2(source: OrganRegistrySourceV2) -> bytes:
    return canonical_json_bytes(source.model_dump(mode="json")) + b"\n"


def _migrate_record(record: OrganRecord) -> OrganRecordV2:
    grouped: dict[tuple[PolicyFamily, str], list[CapabilityContract]] = {}
    for capability in record.capabilities:
        key = (capability.policy_family, capability.credential_class)
        grouped.setdefault(key, []).append(capability)
    contours: list[OrganContourRecord] = []
    for (policy_family, credential_class), capabilities in sorted(grouped.items()):
        allowlist = tuple(
            sorted(
                primitive.mcp_name or primitive.primitive_id
                for capability in capabilities
                for primitive in capability.primitives
            )
        )
        package = record.revisions.package
        deploy = record.revisions.deploy
        contours.append(
            OrganContourRecord(
                contour_id=policy_family,
                registry_state=record.registry_state,
                authority_class=policy_family,
                policy_family=policy_family,
                credential_class=credential_class,
                principal_id=f"{record.organ_id}-{policy_family}",
                allowlist=allowlist,
                capabilities=tuple(capabilities),
                endpoint=record.endpoint,
                runtime_identity=ContourRuntimeIdentity(
                    source_revision=record.revisions.source.revision,
                    source_tree_digest=record.revisions.source.digest,
                    package_name=f"{record.organ_id}-mcp",
                    package_version=(
                        package.revision if package is not None else "unobserved"
                    ),
                    package_digest=package.digest if package is not None else None,
                    deployment_revision=(
                        deploy.revision if deploy is not None else None
                    ),
                    deployed_tree_digest=deploy.digest if deploy is not None else None,
                ),
                revisions=record.revisions,
                freshness_policy=record.freshness_policy,
                freshness_state=record.freshness_state,
                freshness_evidence=record.freshness_evidence,
                eval_status=record.eval_status,
                proof_refs=(
                    (record.eval_evidence,) if record.eval_evidence is not None else ()
                ),
                acceptance_refs=_axis_refs(record, "owner_accepted"),
                consumer_compatibility=record.consumer_compatibility,
                maturity=record.maturity,
                activation_preconditions=record.activation_preconditions,
                currentness=(
                    "current"
                    if record.registry_state == "admitted"
                    else (
                        "stale_readable"
                        if record.registry_state in {"shadow", "deprecated"}
                        else "unknown"
                    )
                ),
                currentness_expires_at=_currentness_expiry(record),
                observation_route=f"owner://{record.owners.runtime_owner}/observation/{record.organ_id}/{policy_family}",
                rollback_route=record.rollback_route,
            )
        )
    return OrganRecordV2(
        organ_id=record.organ_id,
        display_name=record.display_name,
        description=record.description,
        owners=record.owners,
        authentication_requirements=record.authentication_requirements,
        support_route=record.support_route,
        handoff=record.handoff,
        contours=tuple(contours),
    )


def _axis_refs(record: OrganRecord, axis: str) -> tuple[QualifiedEvidenceRef, ...]:
    evidence = getattr(record.maturity, axis).evidence
    return (evidence,) if evidence is not None else ()


def _record_expiry(record: OrganRecord) -> datetime:
    expiries = [
        evidence.expires_at
        for evidence in (
            record.freshness_evidence,
            record.eval_evidence,
            *record.activation_preconditions,
        )
        if evidence is not None and evidence.expires_at is not None
    ]
    for axis_name in type(record.maturity).model_fields:
        evidence = getattr(record.maturity, axis_name).evidence
        if evidence is not None and evidence.expires_at is not None:
            expiries.append(evidence.expires_at)
    if not expiries:
        raise OrganRegistryError(
            f"v1 record {record.organ_id!r} has no bounded evidence expiry"
        )
    return min(expiries)


def _currentness_expiry(record: OrganRecord) -> datetime:
    if (
        record.freshness_evidence is not None
        and record.freshness_evidence.expires_at is not None
    ):
        return record.freshness_evidence.expires_at
    return _record_expiry(record)


def _project_contour(
    record: OrganRecordV2,
    contour: OrganContourRecord,
    *,
    registry_id: str,
    source_digest: str,
    compiled_at: datetime,
    expires_at: datetime,
) -> OrganContourProjectionEntry:
    indexed = QualifiedEvidenceRef(
        owner="aoa-sdk",
        evidence_ref=(
            f"registry://{registry_id}/{source_digest}/{record.organ_id}/{contour.contour_id}"
        ),
        revision=source_digest,
        observed_at=compiled_at,
        expires_at=expires_at,
    )
    return OrganContourProjectionEntry(
        organ_id=record.organ_id,
        contour_id=contour.contour_id,
        display_name=record.display_name,
        description=record.description,
        owners=record.owners,
        authentication_requirements=record.authentication_requirements,
        support_route=record.support_route,
        handoff=record.handoff,
        contour=contour,
        discoverable=contour.registry_state not in NON_DISCOVERABLE_STATES,
        projection_index_evidence=MaturityEvidence(
            state="asserted",
            evidence=indexed,
            freshness_policy="registry-projection-expiry-v2",
        ),
    )
