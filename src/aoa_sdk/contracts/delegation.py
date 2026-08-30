"""Provider-neutral delegation class contracts.

The SDK owns the stable distinction between a cheap, parent-retained read
worker and a responsibility-bearing external incarnation.  It validates
owner-qualified references and lifecycle separation, but never selects a
model, launches a runtime, or turns a reference into an acceptance claim.
"""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import Field, RootModel, TypeAdapter, model_validator

from .control_plane import (
    ContentRef,
    Digest,
    NonEmptyStr,
    ProvenanceRef,
    StrictControlPlaneModel,
)


DELEGATION_CLASS_SCHEMA_VERSION: Literal["aoa_delegation_class_v1"] = (
    "aoa_delegation_class_v1"
)
DELEGATION_ADAPTER_SCHEMA_VERSION: Literal["aoa_delegation_adapter_v1"] = (
    "aoa_delegation_adapter_v1"
)
EPHEMERAL_READ_WORKER_VERSION: Literal["ephemeral_read_worker_v1"] = (
    "ephemeral_read_worker_v1"
)
EXTERNAL_INCARNATION_VERSION: Literal["external_incarnation_v1"] = (
    "external_incarnation_v1"
)
CONTINUATION_OBLIGATION_REF_SCHEMA = "aoa_continuation_obligation_v1"

DelegationClassId: TypeAlias = Literal[
    "ephemeral_read_worker_v1", "external_incarnation_v1"
]
DelegationAdapterKind: TypeAlias = Literal["codex_cli", "local_provider"]
DelegationEffectClass: TypeAlias = Literal["read_only", "repo_mutation"]

_ECONOMY_OBSERVATION_SCHEMA = "abyss_delegation_economy_observation_v1"
_EPHEMERAL_RESULT_SCHEMA = "abyss_ephemeral_read_result_v1"
_EXTERNAL_PROCESS_SCHEMA = "abyss_external_incarnation_process_v1"
_EXTERNAL_SESSION_SCHEMA = "abyss_external_incarnation_session_v1"
_EXTERNAL_EVENT_SCHEMA = "abyss_external_incarnation_event_v1"
_EVAL_REF_OWNER = "aoa-evals"
_EVAL_REF_SCHEMA = "eval-verdict-v1"
_CLOSEOUT_REF_OWNER = "goal-owner"
_CLOSEOUT_REF_SCHEMA = "closeout-v1"
_ACCEPTANCE_REF_OWNER = "goal-owner"
_ACCEPTANCE_REF_SCHEMA = "acceptance-v1"


class DelegationAdapterProfile(StrictControlPlaneModel):
    """One concrete runtime adapter viewed through the common class ABI."""

    schema_version: Literal["aoa_delegation_adapter_v1"] = (
        DELEGATION_ADAPTER_SCHEMA_VERSION
    )
    adapter_id: NonEmptyStr
    adapter_kind: DelegationAdapterKind
    delegation_class: DelegationClassId
    implementation_ref: ProvenanceRef
    provider_neutral_abi: Literal[True] = True
    uses_builtin_codex_subagents: Literal[False] = False

    @model_validator(mode="after")
    def validate_adapter_boundary(self) -> DelegationAdapterProfile:
        if self.implementation_ref.owner_repo != "abyss-stack":
            raise ValueError("delegation adapter implementation must remain runtime-owned")
        if self.implementation_ref.owner_repo == "aoa-sdk":
            raise ValueError("SDK must not become the adapter implementation owner")
        return self


class BoundedImmutableInput(StrictControlPlaneModel):
    """Content-addressed input set with an explicit byte ceiling."""

    input_refs: tuple[ProvenanceRef, ...] = Field(min_length=1)
    snapshot_digest: Digest
    max_input_bytes: int = Field(gt=0)
    max_output_bytes: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_input_identity(self) -> BoundedImmutableInput:
        keys = [(item.owner_repo, item.artifact_ref) for item in self.input_refs]
        if len(keys) != len(set(keys)):
            raise ValueError("delegation input refs must be owner-path unique")
        return self


class DelegationLifecycleRefs(StrictControlPlaneModel):
    """Separate optional lifecycle evidence for an external incarnation."""

    eval_ref: ContentRef | None = None
    closeout_ref: ContentRef | None = None
    acceptance_ref: ContentRef | None = None

    @model_validator(mode="after")
    def validate_distinct_lifecycle_evidence(self) -> DelegationLifecycleRefs:
        refs = [
            ref
            for ref in (self.eval_ref, self.closeout_ref, self.acceptance_ref)
            if ref is not None
        ]
        identities = [
            (ref.owner_repo, ref.object_id, ref.schema_version, ref.digest)
            for ref in refs
        ]
        if len(identities) != len(set(identities)):
            raise ValueError("eval, closeout, and acceptance refs must remain distinct")
        expected = (
            ("eval_ref", self.eval_ref, _EVAL_REF_OWNER, _EVAL_REF_SCHEMA),
            ("closeout_ref", self.closeout_ref, _CLOSEOUT_REF_OWNER, _CLOSEOUT_REF_SCHEMA),
            (
                "acceptance_ref",
                self.acceptance_ref,
                _ACCEPTANCE_REF_OWNER,
                _ACCEPTANCE_REF_SCHEMA,
            ),
        )
        for label, ref, owner, schema_version in expected:
            if ref is not None and (
                ref.owner_repo != owner or ref.schema_version != schema_version
            ):
                raise ValueError(
                    f"{label} must retain exact {owner} {schema_version} ownership"
                )
        return self


class _DelegationClassBase(StrictControlPlaneModel):
    """Shared identity and observation fields for both explicit classes."""

    delegation_id: NonEmptyStr
    correlation_id: NonEmptyStr
    delegation_class: DelegationClassId
    parent_holder_ref: ContentRef
    adapter: DelegationAdapterProfile
    economy_observation_ref: ContentRef
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_shared_boundary(self) -> _DelegationClassBase:
        if self.provenance.owner_repo != "aoa-sdk":
            raise ValueError("delegation class provenance must remain with aoa-sdk")
        if self.adapter.delegation_class != self.delegation_class:
            raise ValueError("adapter and delegation class discriminators must match")
        observation = self.economy_observation_ref
        if (
            observation.owner_repo != "abyss-stack"
            or observation.schema_version != _ECONOMY_OBSERVATION_SCHEMA
        ):
            raise ValueError(
                "economy observation must be the exact abyss-stack observation contract"
            )
        return self


class EphemeralReadWorkerV1(_DelegationClassBase):
    """Cheap stateless work that never acquires responsibility."""

    schema_version: Literal["aoa_ephemeral_read_worker_v1"] = (
        "aoa_ephemeral_read_worker_v1"
    )
    delegation_class: Literal["ephemeral_read_worker_v1"] = (
        EPHEMERAL_READ_WORKER_VERSION
    )
    input: BoundedImmutableInput
    result_ref: ContentRef
    stateless: Literal[True] = True
    read_only: Literal[True] = True
    parent_retains_responsibility: Literal[True] = True
    role_formation_allowed: Literal[False] = False
    durable_responsibility_transfer_allowed: Literal[False] = False

    @model_validator(mode="after")
    def validate_ephemeral_boundary(self) -> EphemeralReadWorkerV1:
        if self.adapter.adapter_kind != "local_provider":
            raise ValueError("ephemeral read work must use the local-provider adapter lane")
        result = self.result_ref
        if (
            result.owner_repo != "abyss-stack"
            or result.schema_version != _EPHEMERAL_RESULT_SCHEMA
        ):
            raise ValueError("ephemeral result must remain an abyss-stack content result")
        return self


class ExternalIncarnationV1(_DelegationClassBase):
    """Responsibility-bearing external actor with a separately reviewed return."""

    schema_version: Literal["aoa_external_incarnation_v1"] = (
        "aoa_external_incarnation_v1"
    )
    delegation_class: Literal["external_incarnation_v1"] = (
        EXTERNAL_INCARNATION_VERSION
    )
    role_contract_ref: ProvenanceRef
    actor_mandate_ref: ContentRef
    model_realization_ref: ProvenanceRef
    incarnation_binding_ref: ContentRef
    continuation_ref: ContentRef
    runtime_process_ref: ContentRef
    runtime_session_ref: ContentRef
    runtime_event_refs: tuple[ContentRef, ...] = Field(min_length=1)
    responsibility_transfer_ref: ContentRef
    reviewed_return_ref: ContentRef
    lifecycle: DelegationLifecycleRefs
    allowed_effect_classes: tuple[DelegationEffectClass, ...] = Field(min_length=1)
    stateless: Literal[False] = False
    responsibility_transferred: Literal[True] = True
    reviewed_return_required: Literal[True] = True

    @model_validator(mode="after")
    def validate_external_owner_chain(self) -> ExternalIncarnationV1:
        self._require_provenance_owner(
            self.role_contract_ref, "aoa-agents", "role contract"
        )
        self._require_content_owner(
            self.actor_mandate_ref,
            "aoa-agents",
            "actor-mandate-v1",
            "actor mandate",
        )
        self._require_provenance_owner(
            self.model_realization_ref, "aoa-models", "model realization"
        )
        if self.model_realization_ref.schema_version != "aoa_model_realization_v1":
            raise ValueError("model realization must use the exact aoa-models schema")
        self._require_content_owner(
            self.incarnation_binding_ref,
            "aoa-sdk",
            "aoa_agent_incarnation_binding_v2",
            "incarnation binding",
        )
        self._require_content_owner(
            self.continuation_ref,
            "aoa-sdk",
            CONTINUATION_OBLIGATION_REF_SCHEMA,
            "continuation",
        )
        self._require_content_owner(
            self.runtime_process_ref,
            "abyss-stack",
            _EXTERNAL_PROCESS_SCHEMA,
            "runtime process",
        )
        self._require_content_owner(
            self.runtime_session_ref,
            "abyss-stack",
            _EXTERNAL_SESSION_SCHEMA,
            "runtime session",
        )
        for event_ref in self.runtime_event_refs:
            self._require_content_owner(
                event_ref, "abyss-stack", _EXTERNAL_EVENT_SCHEMA, "runtime event"
            )
        event_ids = [
            (ref.owner_repo, ref.object_id, ref.digest)
            for ref in self.runtime_event_refs
        ]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("runtime event refs must be distinct")
        self._require_content_owner(
            self.responsibility_transfer_ref,
            "aoa-agents",
            "responsibility-transfer-v1",
            "responsibility transfer",
        )
        self._require_content_owner(
            self.reviewed_return_ref,
            "aoa-agents",
            "responsibility-return-disposition-v1",
            "reviewed return",
        )
        if len(self.allowed_effect_classes) != len(set(self.allowed_effect_classes)):
            raise ValueError("external incarnation effect classes must be unique")
        if "external" in self.allowed_effect_classes:
            raise ValueError("external incarnation class cannot grant external effects")
        return self

    @staticmethod
    def _require_provenance_owner(
        ref: ProvenanceRef, owner: str, label: str
    ) -> None:
        if ref.owner_repo != owner:
            raise ValueError(f"{label} must remain owned by {owner}")

    @staticmethod
    def _require_content_owner(
        ref: ContentRef, owner: str, schema_version: str, label: str
    ) -> None:
        if ref.owner_repo != owner or ref.schema_version != schema_version:
            raise ValueError(
                f"{label} must retain exact {owner} {schema_version} ownership"
            )


DelegationClass: TypeAlias = Annotated[
    EphemeralReadWorkerV1 | ExternalIncarnationV1,
    Field(discriminator="delegation_class"),
]


class DelegationEnvelope(RootModel[DelegationClass]):
    """Discriminated provider-neutral envelope for either delegation class."""


def validate_delegation_class(value: object) -> DelegationClass:
    """Validate one class without selecting a runtime or owner."""

    return TypeAdapter(DelegationClass).validate_python(value)
