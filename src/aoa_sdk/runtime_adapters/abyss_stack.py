"""Explicit transport client for the abyss-stack Agent OS runtime bridge."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from ..contracts.control_plane import (
    ApprovalDecision,
    ApprovalRequirement,
    ApprovalRequest,
    CancelCommand,
    CloseoutBundleRef,
    CommandReceipt,
    ExecutionEvent,
    PauseCommand,
    ProvenanceRef,
    RecoverCommand,
    ResumeCommand,
    RunOutcome,
    RunPlan,
    RunStatus,
    RuntimeCommand,
    RuntimeProfile,
    RuntimeSnapshotObservation,
    SessionHandle,
    StartCommand,
)
from ..errors import AoASDKError


ABYSS_STACK_ADAPTER_VERSION: Literal["abyss_stack_agent_os_adapter_v1"] = (
    "abyss_stack_agent_os_adapter_v1"
)
ABYSS_STACK_BINDING_SCHEMA_VERSION: Literal[
    "abyss_stack_agent_os_binding_v1"
] = "abyss_stack_agent_os_binding_v1"
ABYSS_STACK_PROFILE_SCHEMA_VERSION: Literal[
    "abyss_stack_agent_os_runtime_profile_v1"
] = "abyss_stack_agent_os_runtime_profile_v1"
ABYSS_STACK_BRIDGE_RESPONSE_VERSION: Literal[
    "abyss_stack_agent_os_bridge_response_v1"
] = "abyss_stack_agent_os_bridge_response_v1"
ABYSS_STACK_EXTERNAL_CODEX_ADAPTER_VERSION: Literal[
    "abyss_stack_external_codex_agent_v1"
] = "abyss_stack_external_codex_agent_v1"
ABYSS_STACK_EXTERNAL_CODEX_PROFILE_SCHEMA_VERSION: Literal[
    "abyss_stack_external_codex_runtime_profile_v2"
] = "abyss_stack_external_codex_runtime_profile_v2"

AbyssStackOperation = Literal[
    "observe_snapshot",
    "dispatch",
    "approval_requests",
    "approval_decisions",
    "command_receipts",
    "renew_approvals",
    "apply_approval",
    "status",
    "events",
    "outcome",
    "closeout",
]


class AbyssStackAdapterError(AoASDKError):
    """The explicit abyss-stack runtime binding or response is invalid."""


class AbyssStackTransportError(AbyssStackAdapterError):
    """The configured abyss-stack transport failed before a typed response."""


class _StrictAdapterModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RuntimeArtifactLocation(_StrictAdapterModel):
    """One explicit delivery coordinate for a source artifact in the plan."""

    owner_repo: str = Field(min_length=1)
    artifact_ref: str = Field(min_length=1)
    local_path: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_absolute_path(self) -> RuntimeArtifactLocation:
        if not Path(self.local_path).is_absolute():
            raise ValueError("runtime artifact location must be an absolute path")
        return self


class RuntimeABILocation(_StrictAdapterModel):
    """One explicit delivery coordinate for an ABI artifact in the plan."""

    owner_repo: str = Field(min_length=1)
    abi_id: str = Field(min_length=1)
    local_path: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_absolute_path(self) -> RuntimeABILocation:
        if not Path(self.local_path).is_absolute():
            raise ValueError("runtime ABI location must be an absolute path")
        return self


def load_abyss_stack_external_codex_runtime_profile(
    descriptor_path: str | Path,
) -> RuntimeProfile:
    """Load the exact non-selecting profile for an external Codex process.

    The SDK projects runtime compatibility and provenance only.  Model choice,
    reasoning effort, tool-profile selection, launch, and model-fit judgment
    remain explicit caller/runtime/aoa-models responsibilities.
    """

    path = Path(descriptor_path)
    if not path.is_absolute():
        raise AbyssStackAdapterError(
            "external Codex runtime profile path must be absolute"
        )
    try:
        raw = path.read_bytes()
        descriptor = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise AbyssStackAdapterError(
            "external Codex runtime profile descriptor is unavailable"
        ) from exc
    required_fields = {
        "$schema",
        "schema_version",
        "profile_id",
        "runtime_owner",
        "adapter_id",
        "adapter_protocol_version",
        "transport",
        "source_ref",
        "schema_ref",
        "supported_plan_schema_versions",
        "supported_event_schema_versions",
        "supported_effect_classes",
        "process_containment",
        "codex_cli",
        "model_admission",
        "tool_profiles",
        "execution_postures",
        "owner_contracts",
        "result_schema_ref",
        "boundaries",
    }
    boundaries = descriptor.get("boundaries") if isinstance(descriptor, dict) else None
    process_containment = (
        descriptor.get("process_containment")
        if isinstance(descriptor, dict)
        else None
    )
    owner_contracts = (
        descriptor.get("owner_contracts")
        if isinstance(descriptor, dict)
        else None
    )
    if (
        not isinstance(descriptor, dict)
        or set(descriptor) != required_fields
        or descriptor.get("schema_version")
        != ABYSS_STACK_EXTERNAL_CODEX_PROFILE_SCHEMA_VERSION
        or descriptor.get("profile_id")
        != "runtime-profile:abyss-stack-external-codex-agent-v1"
        or descriptor.get("runtime_owner") != "abyss-stack"
        or descriptor.get("adapter_id")
        != ABYSS_STACK_EXTERNAL_CODEX_ADAPTER_VERSION
        or descriptor.get("adapter_protocol_version")
        != "aoa_runtime_adapter_v1"
        or descriptor.get("transport") != "codex_exec_jsonl_v1"
        or not isinstance(descriptor.get("source_ref"), str)
        or not descriptor["source_ref"]
        or not isinstance(descriptor.get("schema_ref"), str)
        or not descriptor["schema_ref"]
        or not isinstance(boundaries, dict)
        or not isinstance(owner_contracts, dict)
        or set(owner_contracts)
        != {"owner_execution_request_schema", "task_local_dag_schema"}
        or boundaries.get("launches_separate_os_process") is not True
        or boundaries.get("uses_builtin_codex_subagents") is not False
        or boundaries.get("uses_tui_transport") is not False
        or boundaries.get("model_fit_authority") is not False
        or boundaries.get("owner_acceptance_authority") is not False
        or boundaries.get("external_effects_enabled") is not False
        or process_containment
        != {
            "strategy": "linux_subreaper_supervisor_v1",
            "supervisor_ref": "external_codex_supervisor.py",
            "parent_death_signal": "SIGTERM",
            "term_timeout_seconds": 3.0,
            "kill_timeout_seconds": 3.0,
            "probe_executable": "/usr/bin/true",
        }
    ):
        raise AbyssStackAdapterError(
            "external Codex runtime profile descriptor identity is invalid"
        )
    for key in (
        "supported_plan_schema_versions",
        "supported_event_schema_versions",
        "supported_effect_classes",
        "execution_postures",
    ):
        values = descriptor.get(key)
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(item, str) or not item for item in values)
            or len(values) != len(set(values))
        ):
            raise AbyssStackAdapterError(
                f"external Codex runtime profile {key} is invalid"
            )
    if "aoa_control_plane_v1" not in descriptor["supported_plan_schema_versions"]:
        raise AbyssStackAdapterError(
            "external Codex runtime profile does not admit this plan schema"
        )
    if "aoa_control_plane_v1" not in descriptor["supported_event_schema_versions"]:
        raise AbyssStackAdapterError(
            "external Codex runtime profile omits control-plane events"
        )
    if not set(descriptor["supported_effect_classes"]).issubset(
        {"read_only", "repo_mutation"}
    ):
        raise AbyssStackAdapterError(
            "external Codex runtime profile admits unsupported effect classes"
        )
    if not set(descriptor["execution_postures"]).issubset(
        {"bounded_execution", "independent_review", "closeout", "ambiguity_stop"}
    ):
        raise AbyssStackAdapterError(
            "external Codex runtime profile admits unsupported execution postures"
        )
    try:
        provenance = ProvenanceRef(
            owner_repo="abyss-stack",
            artifact_ref=(
                "mechanics/governed-execution/parts/external-codex-agent/"
                "runtime-profile.v1.json"
            ),
            source_ref=descriptor["source_ref"],
            artifact_digest="sha256:" + hashlib.sha256(raw).hexdigest(),
            schema_ref=descriptor["schema_ref"],
            schema_version=descriptor["schema_version"],
        )
        return RuntimeProfile(
            profile_id=descriptor["profile_id"],
            runtime_owner=descriptor["runtime_owner"],
            adapter_id=descriptor["adapter_id"],
            adapter_protocol_version=descriptor["adapter_protocol_version"],
            supported_plan_schema_versions=tuple(
                descriptor["supported_plan_schema_versions"]
            ),
            supported_event_schema_versions=tuple(
                descriptor["supported_event_schema_versions"]
            ),
            supported_effect_classes=tuple(descriptor["supported_effect_classes"]),
            provenance=provenance,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AbyssStackAdapterError(
            "external Codex runtime profile violates the SDK projection"
        ) from exc


def load_abyss_stack_runtime_profile(
    descriptor_path: str | Path,
    *,
    constraint_locations: Iterable[RuntimeArtifactLocation],
    scenario_id: str | None = None,
) -> RuntimeProfile:
    """Materialize one exact runtime-owner profile from delivered artifacts."""

    path = Path(descriptor_path)
    if not path.is_absolute():
        raise AbyssStackAdapterError(
            "abyss-stack runtime profile path must be absolute"
        )
    try:
        descriptor = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AbyssStackAdapterError(
            "abyss-stack runtime profile descriptor is unavailable"
        ) from exc
    descriptor_fields = {
        "schema_version",
        "profile_id",
        "runtime_owner",
        "adapter_id",
        "adapter_protocol_version",
        "source_ref",
        "schema_ref",
        "supported_plan_schema_versions",
        "supported_event_schema_versions",
        "supported_effect_classes",
        "required_constraint_artifacts",
        "compatibility",
        "boundaries",
    }
    if (
        not isinstance(descriptor, dict)
        or set(descriptor) != descriptor_fields
        or descriptor.get("schema_version")
        != ABYSS_STACK_PROFILE_SCHEMA_VERSION
        or descriptor.get("profile_id")
        != "runtime-profile:abyss-stack-governed-execution-v1"
        or descriptor.get("runtime_owner") != "abyss-stack"
        or descriptor.get("adapter_id") != ABYSS_STACK_ADAPTER_VERSION
        or descriptor.get("adapter_protocol_version")
        != "aoa_runtime_adapter_v1"
        or not isinstance(descriptor.get("source_ref"), str)
        or not descriptor["source_ref"]
        or not isinstance(descriptor.get("schema_ref"), str)
        or not descriptor["schema_ref"]
        or not isinstance(descriptor.get("compatibility"), list)
        or not descriptor["compatibility"]
        or not isinstance(descriptor.get("boundaries"), dict)
    ):
        raise AbyssStackAdapterError(
            "abyss-stack runtime profile descriptor identity is invalid"
        )
    required_constraints = descriptor.get("required_constraint_artifacts")
    if not isinstance(required_constraints, list) or not required_constraints:
        raise AbyssStackAdapterError(
            "abyss-stack runtime profile has no constraint provenance"
        )
    expected_fields = {
        "owner_repo",
        "artifact_ref",
        "source_ref",
        "schema_ref",
        "schema_version",
    }
    if any(
        not isinstance(item, dict)
        or set(item) != expected_fields
        or any(
            not isinstance(item[field], str) or not item[field]
            for field in expected_fields
        )
        for item in required_constraints
    ):
        raise AbyssStackAdapterError(
            "abyss-stack runtime constraint provenance is invalid"
        )
    locations = tuple(constraint_locations)
    location_by_key = {
        (item.owner_repo, item.artifact_ref): item
        for item in locations
    }
    if len(location_by_key) != len(locations):
        raise AbyssStackAdapterError(
            "abyss-stack runtime constraint locations contain duplicates"
        )
    expected_keys = {
        (item["owner_repo"], item["artifact_ref"])
        for item in required_constraints
    }
    if set(location_by_key) != expected_keys:
        raise AbyssStackAdapterError(
            "abyss-stack runtime constraint locations are incomplete"
        )
    runtime_approval_payloads: tuple[Mapping[str, Any], ...] = ()
    if scenario_id is not None:
        matches = [
            item
            for item in descriptor["compatibility"]
            if isinstance(item, Mapping)
            and item.get("scenario_id") == scenario_id
        ]
        if len(matches) != 1:
            raise AbyssStackAdapterError(
                "abyss-stack runtime profile does not contain one exact "
                "scenario projection"
            )
        raw_requirements = matches[0].get("runtime_approval_requirements")
        approval_fields = {
            "requirement_id",
            "operation",
            "risk_class",
            "applies_to_step_ids",
            "required_evidence_refs",
            "expires_after_seconds",
            "renewable",
        }
        if (
            not isinstance(raw_requirements, list)
            or any(
                not isinstance(item, Mapping)
                or set(item) != approval_fields
                for item in raw_requirements
            )
        ):
            raise AbyssStackAdapterError(
                "abyss-stack runtime approval projection is invalid"
            )
        runtime_approval_payloads = tuple(raw_requirements)
    try:
        constraint_refs = tuple(
            ProvenanceRef(
                owner_repo=item["owner_repo"],
                artifact_ref=item["artifact_ref"],
                source_ref=item["source_ref"],
                artifact_digest=_sha256_file(
                    Path(
                        location_by_key[
                            (item["owner_repo"], item["artifact_ref"])
                        ].local_path
                    )
                ),
                schema_ref=item["schema_ref"],
                schema_version=item["schema_version"],
            )
            for item in required_constraints
        )
        provenance = ProvenanceRef(
            owner_repo="abyss-stack",
            artifact_ref=(
                "mechanics/governed-execution/parts/agent-os-adapter/"
                "runtime-profile.v1.json"
            ),
            source_ref=descriptor["source_ref"],
            artifact_digest=_sha256_file(path),
            schema_ref=descriptor["schema_ref"],
            schema_version=descriptor["schema_version"],
        )
        runtime_approval_requirements = tuple(
            ApprovalRequirement(
                requirement_id=item["requirement_id"],
                approval_owner=provenance,
                operation=item["operation"],
                risk_class=item["risk_class"],
                applies_to_step_ids=tuple(item["applies_to_step_ids"]),
                required_evidence_refs=tuple(
                    ProvenanceRef.model_validate(evidence)
                    for evidence in item["required_evidence_refs"]
                ),
                expires_after_seconds=item["expires_after_seconds"],
                renewable=item["renewable"],
            )
            for item in runtime_approval_payloads
        )
        return RuntimeProfile(
            profile_id=descriptor["profile_id"],
            runtime_owner=descriptor["runtime_owner"],
            adapter_id=descriptor["adapter_id"],
            adapter_protocol_version=descriptor["adapter_protocol_version"],
            supported_plan_schema_versions=tuple(
                descriptor["supported_plan_schema_versions"]
            ),
            supported_event_schema_versions=tuple(
                descriptor["supported_event_schema_versions"]
            ),
            supported_effect_classes=tuple(
                descriptor["supported_effect_classes"]
            ),
            constraint_refs=constraint_refs,
            runtime_approval_requirements=runtime_approval_requirements,
            provenance=provenance,
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise AbyssStackAdapterError(
            "abyss-stack runtime profile artifacts violate the descriptor"
        ) from exc


class AbyssStackRuntimeBinding(_StrictAdapterModel):
    """Caller-authored coordinates constrained by the runtime-owner contract."""

    schema_version: Literal["abyss_stack_agent_os_binding_v1"] = (
        ABYSS_STACK_BINDING_SCHEMA_VERSION
    )
    binding_id: str = Field(min_length=1)
    runtime_owner: Literal["abyss-stack"] = "abyss-stack"
    adapter_id: Literal["abyss_stack_agent_os_adapter_v1"] = (
        ABYSS_STACK_ADAPTER_VERSION
    )
    plan_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    scenario_id: str = Field(min_length=1)
    playbook_id: str = Field(pattern=r"^AOA-P-[0-9]{4}$")
    request_ref: ProvenanceRef
    request_path: str = Field(min_length=1)
    source_locations: tuple[RuntimeArtifactLocation, ...]
    abi_locations: tuple[RuntimeABILocation, ...]
    adapter_contract_ref: ProvenanceRef

    @model_validator(mode="after")
    def validate_binding_shape(self) -> AbyssStackRuntimeBinding:
        if not Path(self.request_path).is_absolute():
            raise ValueError("runtime request path must be absolute")
        source_keys = [
            (item.owner_repo, item.artifact_ref) for item in self.source_locations
        ]
        abi_keys = [(item.owner_repo, item.abi_id) for item in self.abi_locations]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("runtime source locations must be owner-path unique")
        if len(abi_keys) != len(set(abi_keys)):
            raise ValueError("runtime ABI locations must be owner-id unique")
        request_key = (self.request_ref.owner_repo, self.request_ref.artifact_ref)
        matching_request_locations = [
            item
            for item in self.source_locations
            if (item.owner_repo, item.artifact_ref) == request_key
        ]
        if (
            len(matching_request_locations) != 1
            or matching_request_locations[0].local_path != self.request_path
        ):
            raise ValueError(
                "runtime request must have one exact source delivery coordinate"
            )
        if self.adapter_contract_ref.owner_repo != self.runtime_owner:
            raise ValueError("runtime adapter contract must be owned by abyss-stack")
        return self


def assert_abyss_stack_binding_matches_plan(
    binding: AbyssStackRuntimeBinding,
    plan: RunPlan,
    profile: RuntimeProfile,
) -> None:
    """Fail before transport when a caller binding is not the exact plan view."""

    if plan.runtime_profile != profile:
        raise AbyssStackAdapterError(
            "run plan does not bind the configured abyss-stack runtime profile"
        )
    if (
        profile.runtime_owner != "abyss-stack"
        or profile.adapter_id != ABYSS_STACK_ADAPTER_VERSION
    ):
        raise AbyssStackAdapterError(
            "runtime profile is not the exact abyss-stack adapter ABI"
        )
    if binding.plan_digest != plan.plan_digest:
        raise AbyssStackAdapterError("runtime binding does not name the exact plan")
    if binding.scenario_id != plan.scenario_binding.scenario.scenario_id:
        raise AbyssStackAdapterError(
            "runtime binding scenario does not match the exact plan"
        )
    if binding.adapter_contract_ref != profile.provenance:
        raise AbyssStackAdapterError(
            "runtime binding contract ref differs from the profile provenance"
        )
    admitted_input_refs = {
        *plan.scenario_binding.input_refs,
        *(
            item.artifact_ref
            for item in plan.scenario_binding.input_artifact_bindings
        ),
    }
    if binding.request_ref not in admitted_input_refs:
        raise AbyssStackAdapterError(
            "runtime request is not an exact scenario input in the plan"
        )
    if not any(
        binding.request_ref in step.input_refs
        for step in plan.steps
    ):
        raise AbyssStackAdapterError(
            "runtime request is not bound to any admitted plan step"
        )
    expected_sources = {
        (item.owner_repo, item.artifact_ref) for item in plan.snapshot.source_refs
    }
    actual_sources = {
        (item.owner_repo, item.artifact_ref) for item in binding.source_locations
    }
    if actual_sources != expected_sources:
        raise AbyssStackAdapterError(
            "runtime source locations do not cover the exact plan snapshot"
        )
    expected_abis = {
        (item.owner_repo, item.abi_id) for item in plan.snapshot.abi_refs
    }
    actual_abis = {
        (item.owner_repo, item.abi_id) for item in binding.abi_locations
    }
    if actual_abis != expected_abis:
        raise AbyssStackAdapterError(
            "runtime ABI locations do not cover the exact plan snapshot"
        )


@runtime_checkable
class AbyssStackRuntimeTransport(Protocol):
    """One explicit transport into the runtime-owner bridge."""

    def invoke(
        self,
        operation: AbyssStackOperation,
        payload: Mapping[str, Any],
    ) -> Any: ...


class AbyssStackSubprocessTransport:
    """No-shell JSON transport to one exact abyss-stack executable."""

    def __init__(
        self,
        executable: str | Path,
        *,
        state_root: str | Path,
        python_interpreter: str | Path | None = None,
        timeout_seconds: float = 120.0,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self.executable = Path(executable)
        self.state_root = Path(state_root)
        self.python_interpreter = (
            Path(python_interpreter)
            if python_interpreter is not None
            else None
        )
        if not self.executable.is_absolute():
            raise AbyssStackTransportError(
                "abyss-stack bridge executable path must be absolute"
            )
        if not self.state_root.is_absolute():
            raise AbyssStackTransportError(
                "abyss-stack adapter state root must be absolute"
            )
        if (
            self.python_interpreter is not None
            and not self.python_interpreter.is_absolute()
        ):
            raise AbyssStackTransportError(
                "abyss-stack bridge Python interpreter path must be absolute"
            )
        if timeout_seconds <= 0:
            raise AbyssStackTransportError("transport timeout must be positive")
        self.timeout_seconds = timeout_seconds
        self.environment = dict(environment) if environment is not None else None

    def invoke(
        self,
        operation: AbyssStackOperation,
        payload: Mapping[str, Any],
    ) -> Any:
        encoded = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        command = (
            [
                str(self.python_interpreter),
                "-I",
                str(self.executable),
            ]
            if self.python_interpreter is not None
            else [str(self.executable)]
        )
        try:
            completed = subprocess.run(
                [
                    *command,
                    operation,
                    "--state-root",
                    str(self.state_root),
                ],
                input=encoded,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
                env=self.environment,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AbyssStackTransportError(
                f"abyss-stack bridge invocation failed: {type(exc).__name__}"
            ) from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip()[:1000] or "no bridge diagnostic"
            raise AbyssStackTransportError(
                f"abyss-stack bridge rejected {operation}: {detail}"
            )
        try:
            envelope = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AbyssStackTransportError(
                "abyss-stack bridge returned invalid JSON"
            ) from exc
        if not isinstance(envelope, dict):
            raise AbyssStackTransportError(
                "abyss-stack bridge response must be an object"
            )
        if envelope.get("schema_version") != ABYSS_STACK_BRIDGE_RESPONSE_VERSION:
            raise AbyssStackTransportError(
                "abyss-stack bridge response version is not supported"
            )
        if envelope.get("ok") is not True:
            code = str(envelope.get("error_code") or "bridge_error")
            raise AbyssStackTransportError(
                f"abyss-stack bridge returned a typed error: {code}"
            )
        if "result" not in envelope:
            raise AbyssStackTransportError(
                "abyss-stack bridge response has no result"
            )
        return envelope["result"]


_ModelT = TypeVar("_ModelT", bound=BaseModel)


class AbyssStackRuntimeAdapter:
    """Typed adapter client; plan-step execution remains in abyss-stack."""

    executes_plan_steps = True
    execution_owner = "abyss-stack"
    transport_only = True

    def __init__(
        self,
        *,
        profile: RuntimeProfile,
        binding: AbyssStackRuntimeBinding,
        transport: AbyssStackRuntimeTransport,
    ) -> None:
        if (
            profile.runtime_owner != "abyss-stack"
            or profile.adapter_id != ABYSS_STACK_ADAPTER_VERSION
        ):
            raise AbyssStackAdapterError(
                "adapter requires an exact abyss-stack runtime profile"
            )
        if binding.adapter_contract_ref != profile.provenance:
            raise AbyssStackAdapterError(
                "binding and runtime profile contract provenance differ"
            )
        self._profile = profile
        self._binding = binding
        self._transport = transport
        self._plans: dict[str, RunPlan] = {}

    @property
    def profile(self) -> RuntimeProfile:
        return self._profile

    @property
    def binding(self) -> AbyssStackRuntimeBinding:
        return self._binding

    def observe_snapshot(
        self,
        plan: RunPlan,
        session: SessionHandle,
    ) -> RuntimeSnapshotObservation:
        self._bind_plan(plan, session)
        return self._model_result(
            "observe_snapshot",
            RuntimeSnapshotObservation,
            plan=plan,
            session=session,
        )

    def dispatch(
        self,
        plan: RunPlan,
        session: SessionHandle,
        command: RuntimeCommand,
    ) -> CommandReceipt:
        self._bind_plan(plan, session)
        command_type: TypeAdapter[RuntimeCommand] = TypeAdapter(
            StartCommand
            | PauseCommand
            | ResumeCommand
            | CancelCommand
            | RecoverCommand
        )
        command_type.validate_python(command)
        return self._model_result(
            "dispatch",
            CommandReceipt,
            plan=plan,
            session=session,
            command=command,
        )

    def approval_requests(
        self,
        session: SessionHandle,
    ) -> Iterable[ApprovalRequest]:
        return self._tuple_result(
            "approval_requests",
            ApprovalRequest,
            session=session,
        )

    def approval_decisions(
        self,
        session: SessionHandle,
    ) -> Iterable[ApprovalDecision]:
        return self._tuple_result(
            "approval_decisions",
            ApprovalDecision,
            session=session,
        )

    def command_receipts(
        self,
        session: SessionHandle,
    ) -> Iterable[CommandReceipt]:
        return self._tuple_result(
            "command_receipts",
            CommandReceipt,
            session=session,
        )

    def renew_approvals(
        self,
        plan: RunPlan,
        session: SessionHandle,
        *,
        requested_at: datetime,
    ) -> Iterable[ApprovalRequest]:
        self._bind_plan(plan, session)
        return self._tuple_result(
            "renew_approvals",
            ApprovalRequest,
            plan=plan,
            session=session,
            requested_at=requested_at,
        )

    def apply_approval(
        self,
        plan: RunPlan,
        session: SessionHandle,
        approval: ApprovalDecision,
    ) -> RunStatus:
        self._bind_plan(plan, session)
        return self._model_result(
            "apply_approval",
            RunStatus,
            plan=plan,
            session=session,
            approval=approval,
        )

    def status(self, session: SessionHandle) -> RunStatus:
        return self._model_result("status", RunStatus, session=session)

    def events(
        self,
        session: SessionHandle,
        *,
        after_sequence: int,
    ) -> Iterable[ExecutionEvent]:
        return self._tuple_result(
            "events",
            ExecutionEvent,
            session=session,
            after_sequence=after_sequence,
        )

    def outcome(self, session: SessionHandle) -> RunOutcome | None:
        result = self._invoke("outcome", session=session)
        if result is None:
            return None
        return self._parse_model(RunOutcome, result, "outcome")

    def closeout(
        self,
        plan: RunPlan,
        session: SessionHandle,
        outcome: RunOutcome,
        bundle: CloseoutBundleRef,
    ) -> RunStatus:
        self._bind_plan(plan, session)
        return self._model_result(
            "closeout",
            RunStatus,
            plan=plan,
            session=session,
            outcome=outcome,
            bundle=bundle,
        )

    def _bind_plan(self, plan: RunPlan, session: SessionHandle) -> None:
        assert_abyss_stack_binding_matches_plan(self._binding, plan, self._profile)
        if (
            session.plan_digest != plan.plan_digest
            or session.correlation_id != plan.correlation_id
        ):
            raise AbyssStackAdapterError(
                "session does not bind the exact configured run plan"
            )
        previous = self._plans.get(session.session_id)
        if previous is not None and previous != plan:
            raise AbyssStackAdapterError(
                "adapter session is already bound to another plan"
            )
        self._plans[session.session_id] = plan

    def _plan_for(self, session: SessionHandle) -> RunPlan:
        try:
            plan = self._plans[session.session_id]
        except KeyError as exc:
            raise AbyssStackAdapterError(
                "observe_snapshot or dispatch must bind the session before reads"
            ) from exc
        if (
            session.plan_digest != plan.plan_digest
            or session.correlation_id != plan.correlation_id
        ):
            raise AbyssStackAdapterError("session changed after adapter binding")
        return plan

    def _invoke(self, operation: AbyssStackOperation, **values: Any) -> Any:
        session = values.get("session")
        if not isinstance(session, SessionHandle):
            raise AbyssStackAdapterError("adapter operation requires a session")
        plan = values.get("plan")
        if plan is None:
            plan = self._plan_for(session)
            values["plan"] = plan
        payload = {
            "operation": operation,
            "profile": self._profile.model_dump(mode="json"),
            "binding": self._binding.model_dump(mode="json"),
            **{
                key: _json_value(value)
                for key, value in values.items()
            },
        }
        try:
            return self._transport.invoke(operation, payload)
        except AbyssStackAdapterError:
            raise
        except Exception as exc:
            raise AbyssStackTransportError(
                f"abyss-stack transport raised {type(exc).__name__}"
            ) from exc

    def _model_result(
        self,
        operation: AbyssStackOperation,
        model_type: type[_ModelT],
        **values: Any,
    ) -> _ModelT:
        return self._parse_model(
            model_type,
            self._invoke(operation, **values),
            operation,
        )

    def _tuple_result(
        self,
        operation: AbyssStackOperation,
        model_type: type[_ModelT],
        **values: Any,
    ) -> tuple[_ModelT, ...]:
        result = self._invoke(operation, **values)
        if not isinstance(result, list):
            raise AbyssStackAdapterError(
                f"abyss-stack {operation} result is not a typed sequence"
            )
        return tuple(
            self._parse_model(model_type, item, operation)
            for item in result
        )

    @staticmethod
    def _parse_model(
        model_type: type[_ModelT],
        result: Any,
        operation: str,
    ) -> _ModelT:
        try:
            return model_type.model_validate(result)
        except Exception as exc:
            raise AbyssStackAdapterError(
                f"abyss-stack {operation} result violates {model_type.__name__}"
            ) from exc


def _json_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
