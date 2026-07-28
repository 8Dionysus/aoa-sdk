"""Deterministic host-visible orchestration across owner-bounded organs."""

from __future__ import annotations

from ..contracts.control_plane import canonical_digest
from ..contracts.organ_orchestration import (
    CrossOrganOrchestrationRequest,
    CrossOrganOrchestrationRun,
    CrossOrganStage,
    CrossOrganStageObservation,
    HostVisibleStageReceipt,
    OrchestrationRunState,
    StageKind,
    TypedArtifactRef,
)
from ..errors import AoASDKError
from .registry import sha256_digest


class OrganOrchestrationError(AoASDKError, ValueError):
    """A cross-organ observation or receipt violates the pinned chain."""


_AWAITING_STATES: tuple[OrchestrationRunState, ...] = (
    "awaiting_kag_evidence",
    "awaiting_memo_candidate",
    "awaiting_eval_request",
    "awaiting_eval_result",
    "awaiting_owner_acceptance",
)
_STAGE_KINDS: tuple[StageKind, ...] = (
    "kag_evidence",
    "memo_candidate",
    "eval_request",
    "eval_result",
    "owner_acceptance",
)
_SUCCESS_OUTCOMES = {
    "kag_evidence": "observed",
    "memo_candidate": "candidate_created",
    "eval_request": "request_created",
    "eval_result": "validated",
    "owner_acceptance": "accepted",
}


def start_orchestration(
    request: CrossOrganOrchestrationRequest,
) -> CrossOrganOrchestrationRun:
    """Create the empty content-addressed run without invoking an owner."""

    request_digest = canonical_digest(request)
    run_id = sha256_digest(
        {
            "schema_version": "aoa_cross_organ_orchestration_run_v1",
            "request_id": request.request_id,
            "request_digest": request_digest,
            "control_owner": request.owners.control_owner,
            "host_id": request.host_id,
        }
    )
    return _build_run(
        run_id=run_id,
        request_digest=request_digest,
        request=request,
        stages=(),
        state="awaiting_kag_evidence",
        next_stage_kind="kag_evidence",
        next_owner=request.owners.evidence_owner,
        stop_reason_codes=(),
    )


def advance_orchestration(
    run: CrossOrganOrchestrationRun,
    observation: CrossOrganStageObservation,
) -> CrossOrganOrchestrationRun:
    """Append one owner observation after validating every visible boundary."""

    validate_orchestration_run(run)
    return _advance_validated(run, observation)


def validate_orchestration_run(
    run: CrossOrganOrchestrationRun,
) -> CrossOrganOrchestrationRun:
    """Rebuild the complete chain and reject any semantic or digest drift."""

    rebuilt = start_orchestration(run.request)
    if rebuilt.run_id != run.run_id or rebuilt.request_digest != run.request_digest:
        raise OrganOrchestrationError("run identity does not match its request")
    for stage in run.stages:
        rebuilt = _advance_validated(rebuilt, stage.observation)
    if rebuilt != run:
        raise OrganOrchestrationError(
            "orchestration run does not match its deterministic receipt chain"
        )
    return run


def assert_stage_receipt_digest(receipt: HostVisibleStageReceipt) -> None:
    expected = canonical_digest(receipt, exclude={"receipt_digest"})
    if receipt.receipt_digest != expected:
        raise OrganOrchestrationError(
            f"stage receipt digest mismatch: expected {expected}, "
            f"got {receipt.receipt_digest}"
        )


def _advance_validated(
    run: CrossOrganOrchestrationRun,
    observation: CrossOrganStageObservation,
) -> CrossOrganOrchestrationRun:
    sequence = len(run.stages)
    if run.state not in _AWAITING_STATES or run.next_stage_kind is None:
        raise OrganOrchestrationError(
            f"terminal orchestration state {run.state!r} cannot advance"
        )
    if sequence >= len(run.request.stage_contracts):
        raise OrganOrchestrationError("orchestration has no remaining stage")
    contract = run.request.stage_contracts[sequence]
    if run.state != _AWAITING_STATES[sequence]:
        raise OrganOrchestrationError("run state does not match its stage sequence")
    if run.next_stage_kind != contract.stage_kind:
        raise OrganOrchestrationError("next stage does not match the pinned contract")
    if run.next_owner != contract.owner:
        raise OrganOrchestrationError("next owner does not match the pinned contract")

    expected_input = (
        run.request.root_input
        if sequence == 0
        else run.stages[-1].observation.output_ref
    )
    if observation.stage_kind != contract.stage_kind:
        raise OrganOrchestrationError("observation stage kind is out of order")
    if observation.stage_owner != contract.owner:
        raise OrganOrchestrationError("observation came from the wrong owner")
    if observation.input_ref != expected_input:
        raise OrganOrchestrationError(
            "stage input is not the exact previous output artifact"
        )
    if observation.output_ref.ref_kind != contract.output_ref_kind:
        raise OrganOrchestrationError("stage output kind is not pinned by the request")
    if observation.output_schema_identity != contract.output_schema:
        raise OrganOrchestrationError("stage output schema identity drifted")
    if observation.output_ref.schema_identity != contract.output_schema:
        raise OrganOrchestrationError("output artifact uses an unpinned schema")
    if observation.source_revision != contract.output_schema.source_revision:
        raise OrganOrchestrationError("stage source revision drifted")
    if observation.authority_ceiling != contract.authority_ceiling:
        raise OrganOrchestrationError("stage authority exceeds or changes its ceiling")
    if observation.effect_class != contract.effect_class:
        raise OrganOrchestrationError("stage effect class changed")

    _assert_times(run, observation, expected_input)
    _assert_evidence_current(observation)
    _assert_receipt(run, observation)
    _assert_transition(sequence, contract.next_owner, observation)

    previous_stage_digest = (
        run.stages[-1].stage_digest if run.stages else None
    )
    placeholder = CrossOrganStage(
        sequence=sequence,
        previous_stage_digest=previous_stage_digest,
        stage_digest="sha256:" + ("0" * 64),
        observation=observation,
    )
    stage = placeholder.model_copy(
        update={
            "stage_digest": canonical_digest(
                placeholder,
                exclude={"stage_digest"},
            )
        }
    )
    stages = (*run.stages, stage)

    if observation.transition_state == "stopped":
        state: OrchestrationRunState = "stopped"
        next_stage = None
        next_owner = None
    elif observation.transition_state == "denied":
        state = "denied"
        next_stage = None
        next_owner = None
    elif observation.transition_state == "accepted_terminal":
        state = "accepted"
        next_stage = None
        next_owner = None
    elif observation.transition_state == "rejected_terminal":
        state = "rejected"
        next_stage = None
        next_owner = None
    else:
        state = _AWAITING_STATES[sequence + 1]
        next_stage = _STAGE_KINDS[sequence + 1]
        next_owner = contract.next_owner

    return _build_run(
        run_id=run.run_id,
        request_digest=run.request_digest,
        request=run.request,
        stages=stages,
        state=state,
        next_stage_kind=next_stage,
        next_owner=next_owner,
        stop_reason_codes=observation.stop_reason_codes,
    )


def _assert_times(
    run: CrossOrganOrchestrationRun,
    observation: CrossOrganStageObservation,
    input_ref: TypedArtifactRef,
) -> None:
    if observation.observed_at < run.request.created_at:
        raise OrganOrchestrationError("stage predates the orchestration request")
    if observation.observed_at >= run.request.expires_at:
        raise OrganOrchestrationError("stage was observed after request expiry")
    if observation.expires_at > run.request.expires_at:
        raise OrganOrchestrationError("stage outlives the orchestration request")
    if observation.output_ref.created_at > observation.observed_at:
        raise OrganOrchestrationError("stage output is from the future")
    if observation.output_ref.created_at < input_ref.created_at:
        raise OrganOrchestrationError("stage output predates its input")
    if (
        input_ref.expires_at is not None
        and input_ref.expires_at <= observation.observed_at
    ):
        raise OrganOrchestrationError("stage input is expired")
    if (
        observation.output_ref.expires_at is not None
        and observation.output_ref.expires_at < observation.expires_at
    ):
        raise OrganOrchestrationError(
            "stage claims freshness beyond the output artifact expiry"
        )
    if observation.receipt.issued_at < observation.observed_at:
        raise OrganOrchestrationError("host receipt predates the owner observation")
    if observation.receipt.issued_at >= run.request.expires_at:
        raise OrganOrchestrationError("host receipt was issued after request expiry")
    if observation.receipt.issued_at >= observation.expires_at:
        raise OrganOrchestrationError("host receipt was issued after stage expiry")
    if run.stages:
        previous = run.stages[-1].observation
        if observation.observed_at < previous.receipt.issued_at:
            raise OrganOrchestrationError(
                "stage observation predates the previous host receipt"
            )


def _assert_evidence_current(
    observation: CrossOrganStageObservation,
) -> None:
    if not any(
        evidence.owner == observation.stage_owner
        for evidence in observation.evidence_refs
    ):
        raise OrganOrchestrationError(
            "stage requires evidence qualified by its owner"
        )
    for evidence in observation.evidence_refs:
        if evidence.observed_at > observation.observed_at:
            raise OrganOrchestrationError("stage evidence is from the future")
        if (
            evidence.expires_at is not None
            and evidence.expires_at <= observation.observed_at
        ):
            raise OrganOrchestrationError("stage evidence is expired")
        if (
            evidence.expires_at is not None
            and evidence.expires_at < observation.expires_at
        ):
            raise OrganOrchestrationError(
                "stage claims freshness beyond its evidence expiry"
            )


def _assert_receipt(
    run: CrossOrganOrchestrationRun,
    observation: CrossOrganStageObservation,
) -> None:
    receipt = observation.receipt
    assert_stage_receipt_digest(receipt)
    if receipt.host_id != run.request.host_id:
        raise OrganOrchestrationError("receipt host does not match the request")
    if receipt.run_id != run.run_id:
        raise OrganOrchestrationError("receipt run identity does not match")
    if receipt.previous_snapshot_digest != run.snapshot_digest:
        raise OrganOrchestrationError(
            "receipt does not bind the previous run snapshot"
        )


def _assert_transition(
    sequence: int,
    expected_next_owner: str | None,
    observation: CrossOrganStageObservation,
) -> None:
    if sequence < 4 and observation.transition_state in {
        "accepted_terminal",
        "rejected_terminal",
    }:
        raise OrganOrchestrationError(
            "only the acceptance owner can close the chain"
        )
    if sequence == 4 and observation.transition_state == "proceed":
        raise OrganOrchestrationError("the owner-acceptance stage must be terminal")
    if observation.transition_state == "proceed":
        if observation.next_owner != expected_next_owner:
            raise OrganOrchestrationError("stage returned the wrong next owner")
        expected_outcome = _SUCCESS_OUTCOMES[observation.stage_kind]
        if observation.receipt.outcome != expected_outcome:
            raise OrganOrchestrationError(
                "successful stage receipt has the wrong outcome"
            )
    elif observation.transition_state == "accepted_terminal":
        if observation.receipt.outcome != "accepted":
            raise OrganOrchestrationError("accepted stage needs an accepted receipt")
        _assert_explicit_owner_decision(observation)
    elif observation.transition_state == "rejected_terminal":
        if observation.receipt.outcome != "rejected":
            raise OrganOrchestrationError("rejected stage needs a rejected receipt")
        _assert_explicit_owner_decision(observation)
    elif observation.transition_state == "stopped":
        if observation.receipt.outcome != "stopped":
            raise OrganOrchestrationError("stopped stage needs a stopped receipt")
    elif observation.receipt.outcome != "denied":
        raise OrganOrchestrationError("denied stage needs a denied receipt")


def _assert_explicit_owner_decision(
    observation: CrossOrganStageObservation,
) -> None:
    if observation.review_ref is None:
        raise OrganOrchestrationError(
            "owner acceptance or rejection requires an explicit review ref"
        )
    if observation.review_ref.owner != observation.stage_owner:
        raise OrganOrchestrationError("owner review ref came from the wrong owner")
    if observation.review_ref.observed_at > observation.observed_at:
        raise OrganOrchestrationError("owner review ref is from the future")
    if (
        observation.review_ref.expires_at is not None
        and observation.review_ref.expires_at <= observation.observed_at
    ):
        raise OrganOrchestrationError("owner review ref is expired")
    if not any(
        item.owner == observation.stage_owner
        and item.artifact_digest == observation.output_ref.artifact_digest
        and item.schema_identity == observation.output_schema_identity
        for item in observation.receipt.owner_receipt_refs
    ):
        raise OrganOrchestrationError(
            "host receipt does not include the exact owner decision receipt"
        )


def _build_run(
    *,
    run_id: str,
    request_digest: str,
    request: CrossOrganOrchestrationRequest,
    stages: tuple[CrossOrganStage, ...],
    state: OrchestrationRunState,
    next_stage_kind: StageKind | None,
    next_owner: str | None,
    stop_reason_codes: tuple[str, ...],
) -> CrossOrganOrchestrationRun:
    placeholder = CrossOrganOrchestrationRun(
        run_id=run_id,
        request_digest=request_digest,
        request=request,
        stages=stages,
        snapshot_digest="sha256:" + ("0" * 64),
        state=state,
        next_stage_kind=next_stage_kind,
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
