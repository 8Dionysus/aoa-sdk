"""Exact admitted aoa-playbooks inputs for deterministic plan compilation."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError as JSONSchemaError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ...contracts.control_plane import ABIRef, Digest, ProvenanceRef
from ...errors import AoASDKError


LOCK_RESOURCE = "playbook-plan-contours-source-lock.v1.json"
CONTOUR_RESOURCE = "playbook-plan-contours.v1.json"
SCHEMA_RESOURCE = "playbook-plan-contours.schema.json"
_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_CONTROLS = frozenset({"abi_signature", "slsa_in_toto"})


class PlanCompilationSnapshotError(AoASDKError, ValueError):
    """The pinned plan-contour ABI is absent, stale, or not admitted."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )


class _TrustAdmission(_StrictModel):
    schema_version: Literal["abyss_machine_artifact_trust_gate_v1"]
    consumer_intent: Literal["agent"]
    verdict: Literal["allow"]
    record_id: Digest
    latest_record_id: Digest
    latest_required: Literal[True]
    subject_store_required: Literal[True]
    subject_store_ok: Literal[True]
    subject_store_aggregate_digest: Digest
    required_controls: tuple[str, ...]
    verified_controls: tuple[str, ...]


class _LockedABI(_StrictModel):
    abi_id: Literal["aoa_playbook_plan_contour_v1"]
    abi_version: Literal["aoa_playbook_plan_contour_v1"]
    owner_repo: Literal["aoa-playbooks"]
    schema_ref: str = Field(min_length=1)
    source_ref: str = Field(pattern=r"^[0-9a-f]{40}$")
    artifact_digest: Digest


class _LockedResource(_StrictModel):
    owner_artifact_ref: str = Field(min_length=1)
    packaged_resource: str = Field(min_length=1)
    artifact_digest: Digest
    schema_ref: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)


class PlanContourSourceLock(_StrictModel):
    schema_version: Literal["aoa_control_plane_plan_contour_source_lock_v1"]
    owner_repo: Literal["aoa-playbooks"]
    owner_source_ref: str = Field(pattern=r"^[0-9a-f]{40}$")
    artifact_class: Literal["playbook_registry_bundle"]
    trust_admission: _TrustAdmission
    abi: _LockedABI
    contours: _LockedResource
    schema_resource: _LockedResource = Field(
        alias="schema",
        serialization_alias="schema",
    )


class _InputRef(_StrictModel):
    owner_repo: str = Field(min_length=1)
    artifact_ref: str = Field(min_length=1)


class _ScenarioCondition(_StrictModel):
    condition_id: str = Field(min_length=1)
    binding: Literal["reviewed_boolean"]


class _ContourStep(_StrictModel):
    step_id: str = Field(min_length=1)
    operation_kind: Literal[
        "inspect",
        "mutate",
        "summon",
        "return",
        "validate",
        "evaluate",
        "checkpoint",
        "retain",
        "closeout",
    ]
    effect_class: Literal[
        "read_only",
        "repo_mutation",
        "runtime_mutation",
        "external",
    ]
    depends_on: tuple[str, ...]
    guard_condition_id: str | None
    agent_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]
    input_binding: Literal[
        "none",
        "all_scenario_inputs",
        "selected_scenario_inputs",
    ]
    input_artifact_kinds: tuple[str, ...]
    expected_output_kinds: tuple[str, ...]
    approval_binding: Literal["none", "all_route_requirements"]


class _CheckpointPolicy(_StrictModel):
    owner_binding: Literal["scenario_owner"]
    required_after_step_ids: tuple[str, ...]
    required_on_pause: bool
    required_on_recoverable_failure: bool


class _RetryPolicy(_StrictModel):
    max_attempts: int = Field(ge=1)
    retryable_failure_codes: tuple[str, ...]


class _RollbackPolicy(_StrictModel):
    required: bool
    owner_binding: Literal["scenario_owner", "runtime_owner"]
    trigger_codes: tuple[str, ...]
    rollback_artifact_input_ref: _InputRef | None


class _EvidenceRequirement(_StrictModel):
    requirement_id: str = Field(min_length=1)
    artifact_kind: str = Field(min_length=1)
    artifact_binding: Literal["scenario_input", "step_output"]
    required_after_step_id: str | None
    guard_condition_id: str | None
    terminal_required: bool


class _EvalRequirement(_StrictModel):
    requirement_id: str = Field(min_length=1)
    eval_anchor: str = Field(min_length=1)
    input_ref: _InputRef
    required_evidence_ids: tuple[str, ...]
    guard_condition_id: str | None
    verdict_required_for_closeout: bool


class _RetentionRequirement(_StrictModel):
    requirement_id: str = Field(min_length=1)
    input_ref: _InputRef
    guard_condition_id: str | None
    receipt_required_for_closeout: bool


class _CloseoutRequirement(_StrictModel):
    requirement_id: str = Field(min_length=1)
    owner_binding: Literal["scenario_owner", "runtime_owner"]
    required_ref_kinds: tuple[str, ...]


class PlanContour(_StrictModel):
    playbook_id: str = Field(pattern=r"^AOA-P-[0-9]{4}$")
    playbook_name: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    source_playbook_ref: str = Field(min_length=1)
    required_agent_ids: tuple[str, ...]
    required_capability_ids: tuple[str, ...]
    expected_artifact_kinds: tuple[str, ...]
    input_artifact_kinds: tuple[str, ...]
    scenario_conditions: tuple[_ScenarioCondition, ...]
    steps: tuple[_ContourStep, ...]
    checkpoint_policy: _CheckpointPolicy
    retry_policy: _RetryPolicy
    rollback_policy: _RollbackPolicy
    evidence_requirements: tuple[_EvidenceRequirement, ...]
    eval_requirements: tuple[_EvalRequirement, ...]
    retention_requirements: tuple[_RetentionRequirement, ...]
    closeout_requirements: tuple[_CloseoutRequirement, ...]

    @model_validator(mode="after")
    def validate_internal_refs(self) -> PlanContour:
        unique_fields = {
            "required agents": self.required_agent_ids,
            "required capabilities": self.required_capability_ids,
            "expected artifacts": self.expected_artifact_kinds,
            "input artifacts": self.input_artifact_kinds,
            "conditions": tuple(item.condition_id for item in self.scenario_conditions),
            "steps": tuple(item.step_id for item in self.steps),
        }
        for label, values in unique_fields.items():
            if len(values) != len(set(values)):
                raise ValueError(f"contour {label} must be unique")
        agent_ids = set(self.required_agent_ids)
        capability_ids = set(self.required_capability_ids)
        artifact_kinds = set(self.expected_artifact_kinds)
        input_kinds = set(self.input_artifact_kinds)
        condition_ids = {item.condition_id for item in self.scenario_conditions}
        step_ids = {item.step_id for item in self.steps}
        seen_steps: set[str] = set()
        step_by_id: dict[str, _ContourStep] = {}
        for step in self.steps:
            if not set(step.depends_on).issubset(seen_steps):
                raise ValueError(
                    f"contour step {step.step_id!r} must depend only on "
                    "earlier known steps"
                )
            if (
                step.guard_condition_id is not None
                and step.guard_condition_id not in condition_ids
            ):
                raise ValueError(f"contour step {step.step_id!r} has an unknown guard")
            if not set(step.agent_ids).issubset(agent_ids):
                raise ValueError(f"contour step {step.step_id!r} has an unknown agent")
            if not set(step.capability_ids).issubset(capability_ids):
                raise ValueError(
                    f"contour step {step.step_id!r} has an unknown capability"
                )
            if not set(step.expected_output_kinds).issubset(artifact_kinds):
                raise ValueError(
                    f"contour step {step.step_id!r} has an unknown output kind"
                )
            if step.input_binding == "selected_scenario_inputs":
                if not step.input_artifact_kinds or not set(
                    step.input_artifact_kinds
                ).issubset(input_kinds):
                    raise ValueError(
                        f"contour step {step.step_id!r} has invalid selected inputs"
                    )
            elif step.input_artifact_kinds:
                raise ValueError(
                    f"contour step {step.step_id!r} has hidden input kinds"
                )
            seen_steps.add(step.step_id)
            step_by_id[step.step_id] = step
        if not set(self.checkpoint_policy.required_after_step_ids).issubset(step_ids):
            raise ValueError("contour checkpoint policy has an unknown step")

        evidence_ids = tuple(item.requirement_id for item in self.evidence_requirements)
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("contour evidence requirement ids must be unique")
        for evidence_requirement in self.evidence_requirements:
            if (
                evidence_requirement.guard_condition_id is not None
                and evidence_requirement.guard_condition_id not in condition_ids
            ):
                raise ValueError(
                    f"contour evidence {evidence_requirement.requirement_id!r} "
                    "has an unknown guard"
                )
            if (
                evidence_requirement.required_after_step_id is not None
                and evidence_requirement.required_after_step_id not in step_ids
            ):
                raise ValueError(
                    f"contour evidence {evidence_requirement.requirement_id!r} "
                    "has an unknown step"
                )
            if evidence_requirement.artifact_binding == "scenario_input":
                if evidence_requirement.artifact_kind not in input_kinds:
                    raise ValueError(
                        "contour evidence "
                        f"{evidence_requirement.requirement_id!r} "
                        "has an unknown scenario input"
                    )
            elif (
                evidence_requirement.required_after_step_id is None
                or evidence_requirement.artifact_kind
                not in step_by_id[
                    evidence_requirement.required_after_step_id
                ].expected_output_kinds
            ):
                raise ValueError(
                    f"contour evidence {evidence_requirement.requirement_id!r} "
                    "does not bind a declared step output"
                )

        all_requirement_ids = list(evidence_ids)
        for label, requirements in (
            ("eval", self.eval_requirements),
            ("retention", self.retention_requirements),
            ("closeout", self.closeout_requirements),
        ):
            ids = tuple(item.requirement_id for item in requirements)
            if len(ids) != len(set(ids)):
                raise ValueError(f"contour {label} requirement ids must be unique")
            all_requirement_ids.extend(ids)
        if len(all_requirement_ids) != len(set(all_requirement_ids)):
            raise ValueError("contour requirement ids must be globally unique")
        evidence_id_set = set(evidence_ids)
        for eval_requirement in self.eval_requirements:
            if (
                eval_requirement.guard_condition_id is not None
                and eval_requirement.guard_condition_id not in condition_ids
            ):
                raise ValueError(
                    f"contour eval {eval_requirement.requirement_id!r} "
                    "has an unknown guard"
                )
            if not set(eval_requirement.required_evidence_ids).issubset(
                evidence_id_set
            ):
                raise ValueError(
                    f"contour eval {eval_requirement.requirement_id!r} "
                    "has unknown evidence"
                )
        for retention_requirement in self.retention_requirements:
            if (
                retention_requirement.guard_condition_id is not None
                and retention_requirement.guard_condition_id not in condition_ids
            ):
                raise ValueError(
                    "contour retention "
                    f"{retention_requirement.requirement_id!r} "
                    "has an unknown guard"
                )
        for closeout_requirement in self.closeout_requirements:
            if not set(closeout_requirement.required_ref_kinds).issubset(
                artifact_kinds
            ):
                raise ValueError(
                    f"contour closeout {closeout_requirement.requirement_id!r} "
                    "has an unknown artifact kind"
                )
        return self


class _ContourABI(_StrictModel):
    abi_id: Literal["aoa_playbook_plan_contour_v1"]
    abi_version: Literal["aoa_playbook_plan_contour_v1"]
    owner_repo: Literal["aoa-playbooks"]
    schema_ref: str = Field(min_length=1)


class _SourceOfTruth(_StrictModel):
    config: str = Field(min_length=1)
    playbooks: str = Field(min_length=1)
    schema_ref: str = Field(
        min_length=1,
        alias="schema",
        serialization_alias="schema",
    )


class _PlanContourDocument(_StrictModel):
    schema_version: Literal["aoa_playbook_plan_contours_v1"]
    layer: Literal["aoa-playbooks"]
    abi: _ContourABI
    source_of_truth: _SourceOfTruth
    contours: tuple[PlanContour, ...]


@dataclass(frozen=True, slots=True)
class PlanCompilationSnapshot:
    source_lock: PlanContourSourceLock
    contours: tuple[PlanContour, ...]
    contour_provenance: ProvenanceRef
    schema_provenance: ProvenanceRef
    admission_provenance: ProvenanceRef
    contour_abi: ABIRef
    input_snapshot_digest: str

    def contour_for(self, scenario_id: str) -> PlanContour:
        matches = [
            contour for contour in self.contours if contour.scenario == scenario_id
        ]
        if len(matches) != 1:
            raise PlanCompilationSnapshotError(
                f"expected one admitted contour for scenario {scenario_id!r}, "
                f"found {len(matches)}"
            )
        return matches[0]


def load_plan_compilation_snapshot(
    *,
    resource_root: str | Path | None = None,
) -> PlanCompilationSnapshot:
    """Load and revalidate the immutable plan-contour resources in the SDK."""

    lock_raw = _read_resource(LOCK_RESOURCE, resource_root=resource_root)
    contour_raw = _read_resource(CONTOUR_RESOURCE, resource_root=resource_root)
    schema_raw = _read_resource(SCHEMA_RESOURCE, resource_root=resource_root)
    try:
        source_lock = PlanContourSourceLock.model_validate(
            _decode_object(lock_raw, "plan-contour source lock")
        )
    except ValidationError as exc:
        raise PlanCompilationSnapshotError(
            f"invalid plan-contour source lock: {exc}"
        ) from exc
    _validate_admission(source_lock)
    _assert_digest(
        contour_raw,
        source_lock.contours.artifact_digest,
        "packaged plan contours",
    )
    _assert_digest(
        schema_raw,
        source_lock.schema_resource.artifact_digest,
        "packaged plan-contour schema",
    )
    contour_payload = _decode_object(contour_raw, "packaged plan contours")
    schema_payload = _decode_object(schema_raw, "packaged plan-contour schema")
    try:
        Draft202012Validator.check_schema(schema_payload)
        Draft202012Validator(schema_payload).validate(contour_payload)
    except (SchemaError, JSONSchemaError) as exc:
        raise PlanCompilationSnapshotError(
            f"plan-contour JSON Schema validation failed: {exc}"
        ) from exc
    try:
        document = _PlanContourDocument.model_validate(contour_payload)
    except ValidationError as exc:
        raise PlanCompilationSnapshotError(
            f"plan-contour typed projection failed: {exc}"
        ) from exc
    if (
        document.abi.model_dump()
        != source_lock.abi.model_dump(exclude={"source_ref", "artifact_digest"})
        or source_lock.owner_source_ref != source_lock.abi.source_ref
        or source_lock.contours.schema_ref != document.abi.schema_ref
        or source_lock.schema_resource.owner_artifact_ref != document.abi.schema_ref
        or source_lock.contours.schema_version != document.schema_version
    ):
        raise PlanCompilationSnapshotError(
            "plan-contour ABI identity does not match its exact source lock"
        )
    scenario_ids = [contour.scenario for contour in document.contours]
    playbook_ids = [contour.playbook_id for contour in document.contours]
    if (
        len(scenario_ids) != len(set(scenario_ids))
        or len(playbook_ids) != len(set(playbook_ids))
        or not scenario_ids
    ):
        raise PlanCompilationSnapshotError(
            "plan-contour scenario and playbook identities must be unique"
        )
    contour_provenance = ProvenanceRef(
        owner_repo="aoa-playbooks",
        artifact_ref=source_lock.contours.owner_artifact_ref,
        source_ref=source_lock.owner_source_ref,
        artifact_digest=source_lock.contours.artifact_digest,
        schema_ref=source_lock.contours.schema_ref,
        schema_version=source_lock.contours.schema_version,
    )
    schema_provenance = ProvenanceRef(
        owner_repo="aoa-playbooks",
        artifact_ref=source_lock.schema_resource.owner_artifact_ref,
        source_ref=source_lock.owner_source_ref,
        artifact_digest=source_lock.schema_resource.artifact_digest,
        schema_ref=source_lock.schema_resource.schema_ref,
        schema_version=source_lock.schema_resource.schema_version,
    )
    admission = source_lock.trust_admission
    admission_provenance = ProvenanceRef(
        owner_repo="aoa-playbooks",
        artifact_ref=(
            "dist/abyss-artifact-registry/"
            "aoa-playbooks-playbook-registry/records/"
            f"{admission.record_id.removeprefix('sha256:')}.json"
        ),
        source_ref=source_lock.owner_source_ref,
        artifact_digest=admission.record_id,
        schema_ref="abyss-machine:artifact-bundle-registry-record",
        schema_version="abyss_machine_artifact_bundle_registry_record_v1",
    )
    contour_abi = ABIRef.model_validate(source_lock.abi.model_dump())
    snapshot_identity = {
        "source_lock_digest": _sha256(lock_raw),
        "contour_digest": _sha256(contour_raw),
        "schema_digest": _sha256(schema_raw),
        "trust_record_id": admission.record_id,
        "subject_store_aggregate_digest": (admission.subject_store_aggregate_digest),
    }
    return PlanCompilationSnapshot(
        source_lock=source_lock,
        contours=document.contours,
        contour_provenance=contour_provenance,
        schema_provenance=schema_provenance,
        admission_provenance=admission_provenance,
        contour_abi=contour_abi,
        input_snapshot_digest=_canonical_digest(snapshot_identity),
    )


def _validate_admission(source_lock: PlanContourSourceLock) -> None:
    admission = source_lock.trust_admission
    if admission.record_id != admission.latest_record_id:
        raise PlanCompilationSnapshotError(
            "plan-contour trust record is not the selected latest record"
        )
    required = set(admission.required_controls)
    verified = set(admission.verified_controls)
    if len(required) != len(admission.required_controls) or len(verified) != len(
        admission.verified_controls
    ):
        raise PlanCompilationSnapshotError("plan-contour trust controls must be unique")
    missing = _REQUIRED_CONTROLS - (required & verified)
    if missing:
        raise PlanCompilationSnapshotError(
            f"plan-contour trust controls are incomplete: {sorted(missing)}"
        )
    if not _OID_RE.fullmatch(source_lock.owner_source_ref):
        raise PlanCompilationSnapshotError(
            "plan-contour owner source ref must be an exact Git object id"
        )


def _read_resource(
    name: str,
    *,
    resource_root: str | Path | None,
) -> bytes:
    try:
        if resource_root is not None:
            return (Path(resource_root).resolve() / name).read_bytes()
        resource = resources.files("aoa_sdk.control_plane.planning").joinpath(
            "data", name
        )
        return resource.read_bytes()
    except OSError as exc:
        raise PlanCompilationSnapshotError(
            f"could not read packaged plan-contour resource {name!r}: {exc}"
        ) from exc


def _decode_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlanCompilationSnapshotError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise PlanCompilationSnapshotError(f"{label} must contain a JSON object")
    return payload


def _assert_digest(raw: bytes, expected: str, label: str) -> None:
    actual = _sha256(raw)
    if actual != expected:
        raise PlanCompilationSnapshotError(
            f"{label} digest mismatch: expected {expected}, got {actual}"
        )


def _sha256(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _canonical_digest(payload: object) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(raw)
