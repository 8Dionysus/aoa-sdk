"""Deterministic organ-admission evidence collection and transition preview."""

from __future__ import annotations

from datetime import datetime, timezone

from ..contracts.control_plane import canonical_digest
from ..contracts.organ_admission import (
    AdmissionDecisionReceipt,
    AdmissionDecisionStatement,
    AdmissionAxisAudit,
    AdmissionAxisState,
    AdmissionBaselineStatus,
    AdmissionEvidenceReceipt,
    AdmissionEvidenceStatement,
    AdmissionPreviewAction,
    AdmissionRunState,
    AdmissionStage,
    OrganAdmissionAuthorization,
    OrganAdmissionBaselineAudit,
    OrganAdmissionCandidate,
    OrganAdmissionRequest,
    OrganAdmissionRun,
    RegistryTransitionPreview,
)
from ..contracts.organs import (
    MaturityAxis,
    MaturityEvidence,
    OrganProjectionEntry,
    OrganRecord,
    OrganRegistryProjection,
    QualifiedEvidenceRef,
)
from ..errors import AoASDKError
from .registry import OrganRegistryError, reject_secret_material, sha256_digest


class OrganAdmissionError(AoASDKError, ValueError):
    """One admission receipt, owner boundary, or registry anchor is invalid."""


ADMISSION_STAGES: tuple[AdmissionStage, ...] = (
    "owner_source",
    "reviewed_revision",
    "package",
    "deploy_manifest",
    "deployed_bytes",
    "process_identity",
    "endpoint",
    "observed_schema",
    "auth_contour",
    "consumer_registration",
    "authenticated_canary",
    "owner_grounding_freshness",
    "central_proof",
    "owner_result_acceptance",
    "rollback_proof",
)

_REQUIRED_ADMISSION_AXES: tuple[MaturityAxis, ...] = (
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
    "rollback_proven",
)


def audit_admission_baseline(
    projection: OrganRegistryProjection,
    *,
    organ_id: str,
    capability_id: str,
    evaluated_at: datetime | None = None,
) -> OrganAdmissionBaselineAudit:
    """Report current admission evidence without refreshing or upgrading it."""

    now = _aware_utc(evaluated_at or datetime.now(timezone.utc))
    if projection.expires_at <= now:
        raise OrganAdmissionError("registry projection is expired at baseline audit")
    entry = _find_entry(projection, organ_id)
    capability_present = any(
        item.capability_id == capability_id for item in entry.capabilities
    )
    audits: list[AdmissionAxisAudit] = []
    expired_axes: list[str] = []
    missing_axes: list[str] = []
    for axis in _REQUIRED_ADMISSION_AXES:
        maturity = getattr(entry.maturity, axis)
        evidence = maturity.evidence
        state: AdmissionAxisState
        if maturity.state != "asserted" or evidence is None:
            state = "missing"
            missing_axes.append(axis)
        elif evidence.expires_at is not None and evidence.expires_at <= now:
            state = "expired"
            expired_axes.append(axis)
        else:
            state = "current"
        audits.append(
            AdmissionAxisAudit(
                axis=axis,
                state=state,
                owner=evidence.owner if evidence is not None else None,
                evidence_ref=(
                    evidence.evidence_ref if evidence is not None else None
                ),
                revision=evidence.revision if evidence is not None else None,
                observed_at=evidence.observed_at if evidence is not None else None,
                expires_at=evidence.expires_at if evidence is not None else None,
            )
        )
    reason_codes: list[str] = []
    if not capability_present:
        reason_codes.append("capability_absent")
    if entry.registry_state != "admitted":
        reason_codes.append("registry_state_not_admitted")
    if missing_axes:
        reason_codes.append("required_maturity_evidence_missing")
    if expired_axes:
        reason_codes.append("required_maturity_evidence_expired")
    if entry.freshness_state != "exact":
        reason_codes.append("owner_freshness_not_exact")
    elif (
        entry.freshness_evidence is None
        or (
            entry.freshness_evidence.expires_at is not None
            and entry.freshness_evidence.expires_at <= now
        )
    ):
        reason_codes.append("owner_freshness_evidence_not_current")
    if entry.eval_status != "passed":
        reason_codes.append("central_proof_not_passed")
    elif (
        entry.eval_evidence is None
        or (
            entry.eval_evidence.expires_at is not None
            and entry.eval_evidence.expires_at <= now
        )
    ):
        reason_codes.append("central_proof_evidence_not_current")
    current_consumers = [
        item
        for item in entry.consumer_compatibility
        if item.support_state == "supported"
        and item.evidence_ref is not None
        and (
            item.evidence_ref.expires_at is None
            or item.evidence_ref.expires_at > now
        )
    ]
    if not current_consumers:
        reason_codes.append("supported_consumer_evidence_not_current")
    reason_codes = list(dict.fromkeys(reason_codes))
    status: AdmissionBaselineStatus
    if not capability_present:
        status = "capability_absent"
    elif entry.registry_state != "admitted":
        status = "not_admitted"
    elif reason_codes:
        status = "refresh_required"
    else:
        status = "current"
    placeholder = OrganAdmissionBaselineAudit(
        audit_id="sha256:" + ("0" * 64),
        registry_id=projection.registry_id,
        registry_digest=projection.projection_digest,
        entry_digest=_entry_digest(entry),
        organ_id=entry.organ_id,
        capability_id=capability_id,
        registry_state=entry.registry_state,
        status=status,
        evaluated_at=now,
        projection_expires_at=projection.expires_at,
        capability_present=capability_present,
        axis_audits=tuple(audits),
        reason_codes=tuple(reason_codes),
        admission_current=status == "current",
    )
    return placeholder.model_copy(
        update={
            "audit_id": canonical_digest(placeholder, exclude={"audit_id"})
        }
    )


def start_admission(
    request: OrganAdmissionRequest,
    projection: OrganRegistryProjection,
) -> OrganAdmissionRun:
    """Anchor a resumable deny-default run to one exact registry entry."""

    _reject_admission_secrets(
        request.model_dump(mode="json"), context="admission request"
    )
    _assert_registry_anchor(request, projection)
    return _start_unchecked(request)


def materialize_admission_evidence(
    statement: AdmissionEvidenceStatement,
) -> AdmissionEvidenceReceipt:
    """Address an owner-issued statement without running its owner validator."""

    _reject_admission_secrets(
        statement.model_dump(mode="json"), context="admission evidence"
    )
    return AdmissionEvidenceReceipt.model_validate(
        {
            **statement.model_dump(mode="json"),
            "evidence_id": canonical_digest(statement),
        }
    )


def assert_admission_evidence(
    receipt: AdmissionEvidenceReceipt,
) -> AdmissionEvidenceReceipt:
    statement = AdmissionEvidenceStatement.model_validate(
        receipt.model_dump(mode="json", exclude={"evidence_id"})
    )
    expected = canonical_digest(statement)
    if receipt.evidence_id != expected:
        raise OrganAdmissionError(
            f"admission evidence digest mismatch: expected {expected}, "
            f"got {receipt.evidence_id}"
        )
    _reject_admission_secrets(
        receipt.model_dump(mode="json"), context="admission evidence"
    )
    return receipt


def advance_admission(
    run: OrganAdmissionRun,
    receipt: AdmissionEvidenceReceipt,
) -> OrganAdmissionRun:
    """Append one owner-issued receipt or return the same run on exact replay."""

    validate_admission_run(run)
    return _advance_validated(run, receipt)


def validate_admission_run(run: OrganAdmissionRun) -> OrganAdmissionRun:
    """Rebuild a persisted run and reject snapshot or receipt-chain drift."""

    rebuilt = _start_unchecked(run.request)
    if rebuilt.run_id != run.run_id or rebuilt.request_digest != run.request_digest:
        raise OrganAdmissionError("admission run identity does not match its request")
    for receipt in run.evidence:
        rebuilt = _advance_validated(rebuilt, receipt)
    if rebuilt != run:
        raise OrganAdmissionError(
            "admission run does not match its deterministic evidence chain"
        )
    return run


def build_admission_candidate(
    run: OrganAdmissionRun,
    projection: OrganRegistryProjection,
    *,
    evaluated_at: datetime | None = None,
) -> OrganAdmissionCandidate:
    """Build an immutable transition preview without mutating the registry."""

    validate_admission_run(run)
    if run.state != "ready_for_candidate":
        raise OrganAdmissionError(
            f"incomplete admission run is {run.state!r}, not candidate-ready"
        )
    _assert_registry_anchor(run.request, projection)
    now = _aware_utc(evaluated_at or datetime.now(timezone.utc))
    if now < run.request.requested_at:
        raise OrganAdmissionError("candidate evaluation predates the request")
    if now >= run.request.expires_at:
        raise OrganAdmissionError("admission request expired before candidate build")
    evidence_expiry = min(item.expires_at for item in run.evidence)
    expires_at = min(
        run.request.expires_at,
        projection.expires_at,
        evidence_expiry,
    )
    if expires_at <= now:
        raise OrganAdmissionError("admission evidence expired before candidate build")
    entry = _find_entry(projection, run.request.target.organ_id)
    existing = next(
        (
            item
            for item in entry.capabilities
            if item.capability_id == run.request.target.capability_id
        ),
        None,
    )
    if existing is None:
        action: AdmissionPreviewAction = "add_capability"
    elif existing == run.request.proposed_capability and entry.registry_state == "admitted":
        action = "refresh_admission"
    else:
        action = "replace_capability"
    preview = RegistryTransitionPreview(
        registry_id=projection.registry_id,
        base_registry_digest=projection.projection_digest,
        base_entry_digest=_entry_digest(entry),
        organ_id=entry.organ_id,
        capability_id=run.request.target.capability_id,
        from_state=entry.registry_state,
        action=action,
    )
    placeholder = OrganAdmissionCandidate(
        candidate_id="sha256:" + ("0" * 64),
        run_id=run.run_id,
        run_snapshot_digest=run.snapshot_digest,
        request_digest=run.request_digest,
        target=run.request.target,
        owners=run.request.owners,
        consumer_owner=run.request.consumer_owner,
        operator_owner=run.request.operator_owner,
        evidence_ids=tuple(item.evidence_id for item in run.evidence),
        preview=preview,
        created_at=now,
        expires_at=expires_at,
    )
    return placeholder.model_copy(
        update={
            "candidate_id": canonical_digest(
                placeholder,
                exclude={"candidate_id"},
            )
        }
    )


def assert_admission_candidate(
    candidate: OrganAdmissionCandidate,
) -> OrganAdmissionCandidate:
    expected = canonical_digest(candidate, exclude={"candidate_id"})
    if candidate.candidate_id != expected:
        raise OrganAdmissionError(
            f"admission candidate digest mismatch: expected {expected}, "
            f"got {candidate.candidate_id}"
        )
    _reject_admission_secrets(
        candidate.model_dump(mode="json"), context="admission candidate"
    )
    return candidate


def materialize_admission_decision(
    statement: AdmissionDecisionStatement,
) -> AdmissionDecisionReceipt:
    """Address an independently issued owner or operator decision."""

    _reject_admission_secrets(
        statement.model_dump(mode="json"), context="admission decision"
    )
    return AdmissionDecisionReceipt.model_validate(
        {
            **statement.model_dump(mode="json"),
            "decision_id": canonical_digest(statement),
        }
    )


def assert_admission_decision(
    receipt: AdmissionDecisionReceipt,
) -> AdmissionDecisionReceipt:
    statement = AdmissionDecisionStatement.model_validate(
        receipt.model_dump(mode="json", exclude={"decision_id"})
    )
    expected = canonical_digest(statement)
    if receipt.decision_id != expected:
        raise OrganAdmissionError(
            f"admission decision digest mismatch: expected {expected}, "
            f"got {receipt.decision_id}"
        )
    _reject_admission_secrets(
        receipt.model_dump(mode="json"), context="admission decision"
    )
    return receipt


def authorize_registry_transition(
    run: OrganAdmissionRun,
    candidate: OrganAdmissionCandidate,
    owner_decision: AdmissionDecisionReceipt,
    operator_decision: AdmissionDecisionReceipt,
    target_record: OrganRecord,
    projection: OrganRegistryProjection,
    *,
    evaluated_at: datetime | None = None,
) -> OrganAdmissionAuthorization:
    """Authorize one exact compare-and-swap; never write the registry itself."""

    validate_admission_run(run)
    assert_admission_candidate(candidate)
    assert_admission_decision(owner_decision)
    assert_admission_decision(operator_decision)
    now = _aware_utc(evaluated_at or datetime.now(timezone.utc))
    rebuilt = build_admission_candidate(
        run,
        projection,
        evaluated_at=candidate.created_at,
    )
    if rebuilt != candidate:
        raise OrganAdmissionError("candidate does not match the current run and registry")
    if now < candidate.created_at:
        raise OrganAdmissionError("authorization predates the admission candidate")
    if now >= candidate.expires_at:
        raise OrganAdmissionError("admission candidate is expired")
    _assert_decisions(run, candidate, owner_decision, operator_decision, now)
    _assert_target_record(run, target_record)
    expires_at = min(
        candidate.expires_at,
        owner_decision.expires_at,
        operator_decision.expires_at,
    )
    placeholder = OrganAdmissionAuthorization(
        authorization_id="sha256:" + ("0" * 64),
        candidate_id=candidate.candidate_id,
        owner_decision_id=owner_decision.decision_id,
        operator_decision_id=operator_decision.decision_id,
        target=candidate.target,
        target_record_digest=sha256_digest(target_record.model_dump(mode="json")),
        base_registry_digest=candidate.preview.base_registry_digest,
        base_entry_digest=candidate.preview.base_entry_digest,
        authorized_at=now,
        expires_at=expires_at,
    )
    return placeholder.model_copy(
        update={
            "authorization_id": canonical_digest(
                placeholder,
                exclude={"authorization_id"},
            )
        }
    )


def _start_unchecked(request: OrganAdmissionRequest) -> OrganAdmissionRun:
    request_digest = canonical_digest(request)
    run_id = sha256_digest(
        {
            "schema_version": "aoa_organ_admission_run_v1",
            "request_id": request.request_id,
            "request_digest": request_digest,
            "organ_id": request.target.organ_id,
            "capability_id": request.target.capability_id,
        }
    )
    return _build_run(
        run_id=run_id,
        request_digest=request_digest,
        request=request,
        evidence=(),
        state="collecting",
        next_stage=ADMISSION_STAGES[0],
        next_owner=_expected_owner(request, ADMISSION_STAGES[0]),
        stop_reason_codes=(),
    )


def _advance_validated(
    run: OrganAdmissionRun,
    receipt: AdmissionEvidenceReceipt,
) -> OrganAdmissionRun:
    assert_admission_evidence(receipt)
    existing = next(
        (item for item in run.evidence if item.stage == receipt.stage),
        None,
    )
    if existing is not None:
        if existing == receipt:
            return run
        raise OrganAdmissionError(
            f"conflicting replay for admission stage {receipt.stage!r}"
        )
    if run.state != "collecting" or run.next_stage is None:
        raise OrganAdmissionError(
            f"terminal admission state {run.state!r} cannot advance"
        )
    sequence = len(run.evidence)
    expected_stage = ADMISSION_STAGES[sequence]
    if receipt.stage != expected_stage:
        raise OrganAdmissionError(
            f"admission stage {receipt.stage!r} is out of order; "
            f"expected {expected_stage!r}"
        )
    if receipt.run_id != run.run_id:
        raise OrganAdmissionError("admission evidence belongs to another run")
    if receipt.previous_snapshot_digest != run.snapshot_digest:
        raise OrganAdmissionError("admission evidence does not bind current snapshot")
    if receipt.target != run.request.target:
        raise OrganAdmissionError("admission evidence target drifted")
    expected_owner = _expected_owner(run.request, receipt.stage)
    allowed_owners = _allowed_owners(run.request, receipt.stage)
    if receipt.owner not in allowed_owners:
        raise OrganAdmissionError(
            f"admission stage {receipt.stage!r} came from wrong owner"
        )
    if expected_owner is not None and receipt.stage in {
        "central_proof",
        "owner_result_acceptance",
    } and receipt.owner != expected_owner:
        raise OrganAdmissionError(
            f"admission stage {receipt.stage!r} requires exact owner "
            f"{expected_owner!r}"
        )
    if receipt.stage in {"central_proof", "owner_result_acceptance"} and (
        receipt.owner == run.request.owners.control_owner
    ):
        raise OrganAdmissionError("aoa-sdk cannot issue proof or owner acceptance")
    if receipt.validator not in run.request.owner_validator_bindings:
        raise OrganAdmissionError("admission evidence uses an unpinned owner validator")
    if receipt.observed_at < run.request.requested_at:
        raise OrganAdmissionError("admission evidence predates its request")
    if receipt.observed_at >= run.request.expires_at:
        raise OrganAdmissionError("admission evidence was observed after request expiry")
    if receipt.expires_at > run.request.expires_at:
        raise OrganAdmissionError("admission evidence outlives its request")
    if run.evidence and receipt.observed_at < run.evidence[-1].observed_at:
        raise OrganAdmissionError("admission evidence predates the previous stage")

    evidence = (*run.evidence, receipt)
    state: AdmissionRunState
    if receipt.outcome == "blocked":
        state = "blocked"
        next_stage = None
        next_owner = None
    elif receipt.outcome == "rejected":
        state = "rejected"
        next_stage = None
        next_owner = None
    elif len(evidence) == len(ADMISSION_STAGES):
        state = "ready_for_candidate"
        next_stage = None
        next_owner = None
    else:
        state = "collecting"
        next_stage = ADMISSION_STAGES[len(evidence)]
        next_owner = _expected_owner(run.request, next_stage)
    return _build_run(
        run_id=run.run_id,
        request_digest=run.request_digest,
        request=run.request,
        evidence=evidence,
        state=state,
        next_stage=next_stage,
        next_owner=next_owner,
        stop_reason_codes=receipt.reason_codes,
    )


def _build_run(
    *,
    run_id: str,
    request_digest: str,
    request: OrganAdmissionRequest,
    evidence: tuple[AdmissionEvidenceReceipt, ...],
    state: AdmissionRunState,
    next_stage: AdmissionStage | None,
    next_owner: str | None,
    stop_reason_codes: tuple[str, ...],
) -> OrganAdmissionRun:
    placeholder = OrganAdmissionRun(
        run_id=run_id,
        request_digest=request_digest,
        request=request,
        evidence=evidence,
        snapshot_digest="sha256:" + ("0" * 64),
        state=state,
        next_stage=next_stage,
        next_owner=next_owner,
        stop_reason_codes=stop_reason_codes,
    )
    return placeholder.model_copy(
        update={
            "snapshot_digest": canonical_digest(
                placeholder,
                exclude={"snapshot_digest"},
            )
        }
    )


def _assert_registry_anchor(
    request: OrganAdmissionRequest,
    projection: OrganRegistryProjection,
) -> None:
    anchor = request.current_registry
    if projection.registry_id != anchor.registry_id:
        raise OrganAdmissionError("registry id drifted from admission request")
    if projection.projection_digest != anchor.registry_digest:
        raise OrganAdmissionError("registry digest drifted from admission request")
    if projection.compiled_at != anchor.observed_at:
        raise OrganAdmissionError("registry observation time drifted")
    if projection.expires_at != anchor.expires_at:
        raise OrganAdmissionError("registry expiry drifted")
    entry = _find_entry(projection, request.target.organ_id)
    if _entry_digest(entry) != anchor.entry_digest:
        raise OrganAdmissionError("registry entry digest drifted from admission request")
    if entry.registry_state != anchor.entry_state:
        raise OrganAdmissionError("registry entry state drifted from admission request")
    if entry.owners != request.owners:
        raise OrganAdmissionError("registry owner split drifted from admission request")


def _find_entry(
    projection: OrganRegistryProjection,
    organ_id: str,
) -> OrganProjectionEntry:
    for entry in projection.entries:
        if entry.organ_id == organ_id:
            return entry
    raise OrganAdmissionError(f"organ {organ_id!r} is absent from registry projection")


def _entry_digest(entry: OrganProjectionEntry) -> str:
    return sha256_digest(entry.model_dump(mode="json"))


def _allowed_owners(
    request: OrganAdmissionRequest,
    stage: AdmissionStage,
) -> set[str]:
    owners = request.owners
    if stage in {"owner_source", "reviewed_revision"}:
        return {owners.source_owner, owners.acceptance_owner}
    if stage in {"package", "observed_schema", "auth_contour"}:
        return {owners.access_owner, owners.runtime_owner}
    if stage in {
        "deploy_manifest",
        "deployed_bytes",
        "process_identity",
        "endpoint",
        "authenticated_canary",
    }:
        return {owners.runtime_owner}
    if stage == "consumer_registration":
        return {request.consumer_owner, owners.runtime_owner}
    if stage == "rollback_proof":
        return {owners.runtime_owner, owners.proof_owner}
    if stage == "owner_grounding_freshness":
        return {owners.source_owner, owners.acceptance_owner}
    if stage == "central_proof":
        return {owners.proof_owner}
    return {owners.acceptance_owner}


def _expected_owner(
    request: OrganAdmissionRequest,
    stage: AdmissionStage,
) -> str | None:
    owners = request.owners
    if stage in {"owner_source", "reviewed_revision"}:
        return owners.source_owner
    if stage in {"package", "observed_schema", "auth_contour"}:
        return owners.access_owner
    if stage in {
        "deploy_manifest",
        "deployed_bytes",
        "process_identity",
        "endpoint",
        "authenticated_canary",
    }:
        return owners.runtime_owner
    if stage == "consumer_registration":
        return request.consumer_owner
    if stage == "rollback_proof":
        return owners.proof_owner
    if stage == "owner_grounding_freshness":
        return owners.acceptance_owner
    if stage == "central_proof":
        return owners.proof_owner
    return owners.acceptance_owner


def _assert_decisions(
    run: OrganAdmissionRun,
    candidate: OrganAdmissionCandidate,
    owner_decision: AdmissionDecisionReceipt,
    operator_decision: AdmissionDecisionReceipt,
    now: datetime,
) -> None:
    if owner_decision.decision_kind != "owner":
        raise OrganAdmissionError("owner decision has the wrong decision kind")
    if operator_decision.decision_kind != "operator":
        raise OrganAdmissionError("operator decision has the wrong decision kind")
    if owner_decision.issuer != run.request.owners.acceptance_owner:
        raise OrganAdmissionError("owner admission decision came from wrong owner")
    if operator_decision.issuer != run.request.operator_owner:
        raise OrganAdmissionError("operator admission decision came from wrong owner")
    if owner_decision.candidate_id != candidate.candidate_id or (
        operator_decision.candidate_id != candidate.candidate_id
    ):
        raise OrganAdmissionError("admission decision targets another candidate")
    if owner_decision.decision != "accepted" or operator_decision.decision != "accepted":
        raise OrganAdmissionError("registry transition requires both acceptances")
    if owner_decision.decided_at < candidate.created_at or (
        operator_decision.decided_at < candidate.created_at
    ):
        raise OrganAdmissionError("admission decision predates its candidate")
    if owner_decision.expires_at <= now or operator_decision.expires_at <= now:
        raise OrganAdmissionError("admission decision is expired")
    if owner_decision.decision_id == operator_decision.decision_id or (
        owner_decision.decision_ref == operator_decision.decision_ref
    ):
        raise OrganAdmissionError("owner and operator decisions must be separate receipts")


def _assert_target_record(run: OrganAdmissionRun, record: OrganRecord) -> None:
    request = run.request
    target = request.target
    if record.organ_id != target.organ_id:
        raise OrganAdmissionError("target record belongs to another organ")
    if record.owners != request.owners:
        raise OrganAdmissionError("target record owner split drifted")
    if record.registry_state != "admitted":
        raise OrganAdmissionError("target registry record must be admitted")
    capability = next(
        (item for item in record.capabilities if item.capability_id == target.capability_id),
        None,
    )
    if capability != request.proposed_capability:
        raise OrganAdmissionError("target record does not contain exact proposed capability")
    evidence = {item.stage: item for item in run.evidence}
    if record.revisions.source.revision != evidence["owner_source"].subject_revision or (
        record.revisions.source.digest != evidence["owner_source"].subject_digest
    ):
        raise OrganAdmissionError("target source revision does not match admission evidence")
    if record.revisions.package is None or record.revisions.deploy is None:
        raise OrganAdmissionError("target record lacks package/deploy identity")
    if record.revisions.package.digest != evidence["package"].subject_digest:
        raise OrganAdmissionError("target package digest does not match admission evidence")
    if record.revisions.deploy.revision != evidence["deploy_manifest"].subject_revision or (
        record.revisions.deploy.digest != evidence["deployed_bytes"].subject_digest
    ):
        raise OrganAdmissionError("target deploy identity does not match admission evidence")
    if record.endpoint is None:
        raise OrganAdmissionError("target record lacks endpoint")
    if record.endpoint.endpoint_ref != evidence["endpoint"].subject_ref:
        raise OrganAdmissionError("target endpoint does not match admission evidence")
    if record.endpoint.server_schema_digest != evidence["observed_schema"].subject_digest:
        raise OrganAdmissionError("target schema digest does not match admission evidence")
    if target.credential_class != evidence["auth_contour"].subject_revision:
        raise OrganAdmissionError("target credential contour does not match auth evidence")
    consumer_id = evidence["consumer_registration"].subject_revision
    if not any(
        item.consumer_id == consumer_id
        and item.support_state == "supported"
        and item.evidence_ref is not None
        for item in record.consumer_compatibility
    ):
        raise OrganAdmissionError("target record lacks evidenced supported consumer")
    _assert_record_evidence(record.eval_evidence, evidence["central_proof"])
    _assert_record_evidence(
        record.freshness_evidence,
        evidence["owner_grounding_freshness"],
    )
    maturity_map: dict[str, AdmissionStage] = {
        "declared": "owner_source",
        "owner_reviewed": "reviewed_revision",
        "packaged": "package",
        "exported": "deploy_manifest",
        "deployed": "deployed_bytes",
        "process_alive": "process_identity",
        "endpoint_ready": "endpoint",
        "consumer_registered": "consumer_registration",
        "schema_observed": "observed_schema",
        "call_succeeded": "authenticated_canary",
        "result_grounded": "owner_grounding_freshness",
        "freshness_satisfied": "owner_grounding_freshness",
        "owner_accepted": "owner_result_acceptance",
        "rollback_proven": "rollback_proof",
    }
    for axis, stage in maturity_map.items():
        _assert_maturity_evidence(getattr(record.maturity, axis), evidence[stage], axis)


def _assert_record_evidence(
    evidence_ref: QualifiedEvidenceRef | None,
    admission: AdmissionEvidenceReceipt,
) -> None:
    if evidence_ref is None:
        raise OrganAdmissionError("target record omits required owner evidence")
    if (
        evidence_ref.owner,
        evidence_ref.evidence_ref,
        evidence_ref.revision,
    ) != (
        admission.owner,
        admission.evidence_ref,
        admission.evidence_revision,
    ):
        raise OrganAdmissionError("target record evidence does not match receipt chain")


def _assert_maturity_evidence(
    maturity: MaturityEvidence,
    admission: AdmissionEvidenceReceipt,
    axis: str,
) -> None:
    if maturity.state != "asserted" or maturity.evidence is None:
        raise OrganAdmissionError(f"target maturity axis {axis!r} is not asserted")
    try:
        _assert_record_evidence(maturity.evidence, admission)
    except OrganAdmissionError as exc:
        raise OrganAdmissionError(
            f"target maturity axis {axis!r} does not match admission evidence"
        ) from exc


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise OrganAdmissionError("admission timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _reject_admission_secrets(value: object, *, context: str) -> None:
    try:
        reject_secret_material(value, context=context)
    except OrganRegistryError as exc:
        raise OrganAdmissionError(str(exc)) from exc
