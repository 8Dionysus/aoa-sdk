"""Deterministic contour-addressed organ registry compilation and migration."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast

from pydantic import ValidationError

from ..contracts.organ_registry_v2 import (
    ContourRuntimeIdentity,
    OrganContourAdmissionRevision,
    OrganContourSupplement,
    OrganContourShapeRevision,
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
    RevisionIdentity,
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


def rebase_expired_registry_v2_to_shadow(
    source: OrganRegistrySourceV2,
    *,
    authored_at: datetime,
    expires_at: datetime,
    owner_decision_ref: str,
    maximum_ttl: timedelta = timedelta(hours=24),
) -> OrganRegistrySourceV2:
    """Create fresh desired state from an expired registry without claim carryover.

    This is deliberately a destructive reset of *claims*, not a renewal path.
    It preserves owner-declared contour shape, source identity, credential and
    principal boundaries, and operator routes.  Admission, runtime, endpoint,
    freshness, proof, acceptance, consumer, last-good, and maturity evidence
    are removed so every contour must be evidenced again by its stronger owner.
    """

    if authored_at.tzinfo is None or authored_at.utcoffset() is None:
        raise OrganRegistryError("shadow rebase authored_at must be timezone-aware")
    if expires_at.tzinfo is None or expires_at.utcoffset() is None:
        raise OrganRegistryError("shadow rebase expires_at must be timezone-aware")
    authored_at = authored_at.astimezone(timezone.utc)
    expires_at = expires_at.astimezone(timezone.utc)
    if authored_at < source.expires_at:
        raise OrganRegistryError("only an expired registry may be rebased to shadow")
    if expires_at <= authored_at:
        raise OrganRegistryError("shadow rebase expiry must follow authored_at")
    if maximum_ttl <= timedelta(0):
        raise OrganRegistryError("shadow rebase maximum TTL must be positive")
    if expires_at - authored_at > maximum_ttl:
        raise OrganRegistryError("shadow rebase TTL exceeds the configured maximum")

    unknown = MaturityEvidence(state="not_asserted")
    maturity = OrganMaturityVector(
        **{name: unknown for name in OrganMaturityVector.model_fields}
    )
    records: list[OrganRecordV2] = []
    for record in source.records:
        contours: list[OrganContourRecord] = []
        for contour in record.contours:
            source_revision = contour.revisions.source
            contours.append(
                contour.model_copy(
                    update={
                        "registry_state": "shadow",
                        "endpoint": None,
                        "runtime_identity": ContourRuntimeIdentity(
                            source_revision=source_revision.revision,
                            source_tree_digest=source_revision.digest,
                            package_name=contour.runtime_identity.package_name,
                            package_version="unobserved",
                        ),
                        "runtime_identity_evidence": (),
                        "revisions": OrganRevisions(source=source_revision),
                        "freshness_state": "unknown",
                        "freshness_evidence": None,
                        "owner_watermark": None,
                        "owner_watermark_evidence": None,
                        "eval_status": "not_run",
                        "proof_refs": (),
                        "acceptance_refs": (),
                        "consumer_compatibility": (),
                        "maturity": maturity,
                        "activation_preconditions": (),
                        "currentness": "unknown",
                        "currentness_expires_at": expires_at,
                        "last_good": None,
                    }
                )
            )
        records.append(record.model_copy(update={"contours": tuple(contours)}))
    decisions = tuple(
        dict.fromkeys((*source.owner_decision_refs, owner_decision_ref))
    )
    return OrganRegistrySourceV2.model_validate(
        source.model_copy(
            update={
                "authored_at": authored_at,
                "expires_at": expires_at,
                "owner_decision_refs": decisions,
                "records": tuple(records),
            }
        ).model_dump(mode="json")
    )


def apply_registry_runtime_overlay(
    source: OrganRegistrySourceV2,
    overlay: OrganRegistryRuntimeOverlay,
    *,
    applied_at: datetime | None = None,
) -> OrganRegistrySourceV2:
    """Apply exact runtime bindings without changing authority or evidence claims."""

    if applied_at is not None:
        if applied_at.tzinfo is None or applied_at.utcoffset() is None:
            raise OrganRegistryError("runtime overlay applied_at must be timezone-aware")
        applied_at = applied_at.astimezone(timezone.utc)
        if overlay.authored_at > applied_at:
            raise OrganRegistryError("runtime overlay is authored in the future")
        if overlay.expires_at <= applied_at:
            raise OrganRegistryError("runtime overlay is expired")
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


def apply_contour_shape_revision(
    source: OrganRegistrySourceV2,
    revision: OrganContourShapeRevision,
) -> OrganRegistrySourceV2:
    """Replace one owner-declared contour shape and reset it to bare shadow."""

    matches = [item for item in source.records if item.organ_id == revision.organ_id]
    if len(matches) != 1:
        raise OrganRegistryError("shape revision organ is absent or ambiguous")
    target = matches[0]
    if revision.source_owner != target.owners.source_owner:
        raise OrganRegistryError("shape revision source owner is not authoritative")
    contour_matches = [
        item
        for item in target.contours
        if item.contour_id == revision.contour.contour_id
    ]
    if len(contour_matches) != 1:
        raise OrganRegistryError("shape revision contour is absent or ambiguous")
    existing = contour_matches[0]
    existing_digest = sha256_digest(existing.model_dump(mode="json"))
    if existing_digest != revision.expected_contour_digest:
        raise OrganRegistryError("shape revision predecessor digest conflicts")
    evidence_expiry = revision.source_evidence.expires_at or source.expires_at
    currentness_expiry = min(source.expires_at, evidence_expiry)
    unknown = MaturityEvidence(state="not_asserted")
    maturity = OrganMaturityVector(
        **{name: unknown for name in OrganMaturityVector.model_fields}
    )
    replacement = OrganContourRecord(
        contour_id=revision.contour.contour_id,
        registry_state="shadow",
        authority_class=revision.contour.authority_class,
        policy_family=revision.contour.policy_family,
        credential_class=revision.contour.credential_class,
        principal_id=revision.contour.principal_id,
        allowlist=tuple(
            sorted(
                primitive.mcp_name or primitive.primitive_id
                for capability in revision.contour.capabilities
                for primitive in capability.primitives
            )
        ),
        capabilities=revision.contour.capabilities,
        runtime_identity=ContourRuntimeIdentity(
            source_revision=revision.source_revision.revision,
            source_tree_digest=revision.source_revision.digest,
            package_name=existing.runtime_identity.package_name,
            package_version="unobserved",
        ),
        revisions=OrganRevisions(source=revision.source_revision),
        freshness_policy=existing.freshness_policy,
        maturity=maturity,
        currentness="unknown",
        currentness_expires_at=currentness_expiry,
        observation_route=revision.contour.observation_route,
        rollback_route=revision.contour.rollback_route,
    )
    records = tuple(
        record.model_copy(
            update={
                "contours": tuple(
                    replacement if item.contour_id == replacement.contour_id else item
                    for item in record.contours
                )
            }
        )
        if record.organ_id == target.organ_id
        else record
        for record in source.records
    )
    decisions = tuple(
        dict.fromkeys((*source.owner_decision_refs, revision.owner_decision_ref))
    )
    return OrganRegistrySourceV2.model_validate(
        source.model_copy(
            update={"owner_decision_refs": decisions, "records": records}
        ).model_dump(mode="json")
    )


def apply_contour_admission_revision(
    source: OrganRegistrySourceV2,
    revision: OrganContourAdmissionRevision,
    *,
    applied_at: datetime | None = None,
) -> OrganRegistrySourceV2:
    """CAS-admit one contour from separately issued bounded evidence."""

    timestamp = (applied_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if timestamp < revision.issued_at or timestamp >= revision.expires_at:
        raise OrganRegistryError("contour admission revision is not current")
    if timestamp >= source.expires_at:
        raise OrganRegistryError("registry source is expired at admission")
    unsigned = revision.model_dump(mode="json", exclude={"revision_digest"})
    if sha256_digest(unsigned) != revision.revision_digest:
        raise OrganRegistryError("contour admission revision content address is invalid")
    records = [item for item in source.records if item.organ_id == revision.organ_id]
    if len(records) != 1:
        raise OrganRegistryError("admission revision organ is absent or ambiguous")
    record = records[0]
    contours = [
        item for item in record.contours if item.contour_id == revision.contour_id
    ]
    if len(contours) != 1:
        raise OrganRegistryError("admission revision contour is absent or ambiguous")
    contour = contours[0]
    refreshes_expired_admission = (
        contour.registry_state == "admitted"
        and timestamp >= contour.currentness_expires_at
    )
    if contour.registry_state != "shadow" and not refreshes_expired_admission:
        raise OrganRegistryError(
            "only a shadow or expired admitted contour can enter admission"
        )
    if sha256_digest(contour.model_dump(mode="json")) != revision.expected_contour_digest:
        raise OrganRegistryError("admission revision predecessor digest conflicts")
    if contour.endpoint is None:
        raise OrganRegistryError("admission contour endpoint is unavailable")
    runtime = contour.runtime_identity
    if (
        runtime.package_digest is None
        or runtime.deployment_revision is None
        or runtime.deployed_tree_digest is None
        or runtime.deployment_manifest_digest is None
        or (
            contour.registry_state == "shadow"
            and contour.revisions.consumer_schema is not None
        )
    ):
        raise OrganRegistryError(
            "admission contour needs exact runtime identity and an unclaimed consumer slot"
        )
    owners = record.owners
    expected_axis_owners: dict[str, set[str]] = {
        "declared": {owners.source_owner},
        "owner_reviewed": {owners.source_owner, owners.acceptance_owner},
        "packaged": {owners.runtime_owner},
        "exported": {owners.runtime_owner},
        "deployed": {owners.runtime_owner},
        "process_alive": {owners.runtime_owner},
        "endpoint_ready": {owners.runtime_owner},
        "registry_indexed": {owners.control_owner},
        "schema_observed": {owners.runtime_owner},
        "call_succeeded": {owners.runtime_owner},
        "result_grounded": {owners.acceptance_owner},
        "freshness_satisfied": {owners.acceptance_owner},
        "owner_accepted": {owners.acceptance_owner},
        "rollback_proven": {owners.proof_owner},
    }
    evidence: dict[str, QualifiedEvidenceRef | None] = {
        name: cast(MaturityEvidence, getattr(revision.maturity, name)).evidence
        for name in OrganMaturityVector.model_fields
        if name != "cross_organ_proven"
    }
    for axis, allowed in expected_axis_owners.items():
        item = evidence[axis]
        if item is None or item.owner not in allowed:
            raise OrganRegistryError(f"admission axis {axis} has the wrong owner")
    consumer_evidence = revision.consumer_compatibility.evidence_ref
    if (
        consumer_evidence is None
        or evidence["consumer_registered"] != consumer_evidence
    ):
        raise OrganRegistryError("consumer maturity does not match compatibility")
    if revision.proof_ref.owner != owners.proof_owner:
        raise OrganRegistryError("central proof ref has the wrong owner")
    if revision.acceptance_ref.owner != owners.acceptance_owner:
        raise OrganRegistryError("owner acceptance ref has the wrong owner")
    if revision.rollback_ref.owner != owners.proof_owner:
        raise OrganRegistryError("rollback ref has the wrong owner")
    if evidence["owner_accepted"] != revision.acceptance_ref:
        raise OrganRegistryError("owner acceptance maturity differs from receipt")
    if evidence["rollback_proven"] != revision.rollback_ref:
        raise OrganRegistryError("rollback maturity differs from receipt")
    if evidence["freshness_satisfied"] != revision.freshness_evidence:
        raise OrganRegistryError("freshness maturity differs from owner evidence")
    if revision.owner_watermark_evidence != revision.freshness_evidence:
        raise OrganRegistryError("owner watermark evidence differs from freshness")
    if revision.operator_evidence.owner != source.workspace_owner:
        raise OrganRegistryError("operator evidence is not issued by workspace owner")

    all_evidence = (
        revision.operator_evidence,
        revision.proof_ref,
        revision.acceptance_ref,
        revision.rollback_ref,
        revision.freshness_evidence,
        revision.owner_watermark_evidence,
        consumer_evidence,
        *tuple(item for item in evidence.values() if item is not None),
        *revision.last_good.evidence_refs,
    )
    if any(item.observed_at > revision.issued_at for item in all_evidence):
        raise OrganRegistryError("admission evidence postdates operator issuance")
    expiries = [
        item.expires_at for item in all_evidence if item.expires_at is not None
    ]
    expiries.extend((revision.expires_at, revision.last_good.expires_at, source.expires_at))
    currentness_expiry = min(expiries)
    if currentness_expiry <= timestamp:
        raise OrganRegistryError("admission evidence is expired")
    consumer_revision = revision.consumer_compatibility.observed_schema_digest
    assert consumer_revision is not None
    admitted = contour.model_copy(
        update={
            "registry_state": "admitted",
            "revisions": contour.revisions.model_copy(
                update={
                    "package": RevisionIdentity(
                        revision=runtime.deployment_revision,
                        digest=runtime.package_digest,
                    ),
                    "deploy": RevisionIdentity(
                        revision=runtime.deployment_revision,
                        digest=runtime.deployed_tree_digest,
                    ),
                    "consumer_schema": RevisionIdentity(
                        revision=consumer_evidence.revision,
                        schema_digest=consumer_revision,
                    ),
                }
            ),
            "freshness_state": "exact",
            "freshness_evidence": revision.freshness_evidence,
            "owner_watermark": revision.owner_watermark,
            "owner_watermark_evidence": revision.owner_watermark_evidence,
            "eval_status": "passed",
            "proof_refs": (revision.proof_ref,),
            "acceptance_refs": (revision.acceptance_ref,),
            "consumer_compatibility": (revision.consumer_compatibility,),
            "maturity": revision.maturity,
            "activation_preconditions": (
                revision.operator_evidence,
                revision.proof_ref,
                revision.acceptance_ref,
                revision.rollback_ref,
                consumer_evidence,
            ),
            "currentness": "current",
            "currentness_expires_at": currentness_expiry,
            "last_good": revision.last_good,
        }
    )
    updated_records = tuple(
        item.model_copy(
            update={
                "contours": tuple(
                    admitted if candidate.contour_id == admitted.contour_id else candidate
                    for candidate in item.contours
                )
            }
        )
        if item.organ_id == record.organ_id
        else item
        for item in source.records
    )
    decisions = tuple(
        dict.fromkeys(
            (*source.owner_decision_refs, revision.operator_evidence.evidence_ref)
        )
    )
    return OrganRegistrySourceV2.model_validate(
        source.model_copy(
            update={
                "authored_at": timestamp,
                "owner_decision_refs": decisions,
                "records": updated_records,
            }
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
