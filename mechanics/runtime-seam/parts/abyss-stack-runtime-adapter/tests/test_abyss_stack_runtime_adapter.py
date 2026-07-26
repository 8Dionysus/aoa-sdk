from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter

from aoa_sdk.contracts.control_plane import (
    ApprovalDecision,
    ProvenanceRef,
    RunPlan,
    RuntimeCommand,
    RuntimeProfile,
    StartCommand,
    canonical_digest,
)
from aoa_sdk.control_plane.runner import AoARunner, DeterministicReferenceAdapter
from aoa_sdk.runtime_adapters import (
    ABYSS_STACK_ADAPTER_VERSION,
    AbyssStackAdapterError,
    AbyssStackRuntimeAdapter,
    AbyssStackRuntimeBinding,
    AbyssStackSubprocessTransport,
    AbyssStackTransportError,
    RuntimeABILocation,
    RuntimeArtifactLocation,
    assert_abyss_stack_binding_matches_plan,
    load_abyss_stack_runtime_profile,
)


NOW = datetime(2026, 7, 26, 19, 30, tzinfo=timezone.utc)
ZERO_DIGEST = "sha256:" + "0" * 64
EXAMPLE = (
    Path(__file__).resolve().parents[4]
    / "boundary-bridge"
    / "parts"
    / "plan-compilation-control-plane"
    / "examples"
    / "bounded-preview-pruned.run-plan.json"
)


def _digest(value: str) -> str:
    import hashlib

    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()}"


def _stack_contract_ref() -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo="abyss-stack",
        artifact_ref=(
            "mechanics/governed-execution/parts/agent-os-adapter/"
            "runtime-profile.v1.json"
        ),
        source_ref="0c930170c474eaaee1dc71d56ef4e00cc3b7e7e8",
        artifact_digest=_digest("abyss-stack-agent-os-profile"),
        schema_ref=(
            "mechanics/governed-execution/parts/agent-os-adapter/"
            "schemas/agent-os-runtime-profile.schema.json"
        ),
        schema_version="abyss_stack_agent_os_runtime_profile_v1",
    )


def _stack_plan() -> RunPlan:
    original = RunPlan.model_validate_json(EXAMPLE.read_text(encoding="utf-8"))
    contract_ref = _stack_contract_ref()
    profile = RuntimeProfile(
        profile_id="runtime-profile:abyss-stack-governed-execution-v1",
        runtime_owner="abyss-stack",
        adapter_id=ABYSS_STACK_ADAPTER_VERSION,
        supported_plan_schema_versions=("aoa_control_plane_v1",),
        supported_event_schema_versions=("aoa_control_plane_v1",),
        supported_effect_classes=("read_only", "repo_mutation"),
        provenance=contract_ref,
    )
    source_refs = tuple(
        contract_ref if item == original.runtime_profile.provenance else item
        for item in original.snapshot.source_refs
    )
    snapshot = original.snapshot.model_copy(
        update={
            "source_refs": source_refs,
            "snapshot_digest": ZERO_DIGEST,
        }
    )
    snapshot = snapshot.model_copy(
        update={
            "snapshot_digest": canonical_digest(
                snapshot,
                exclude={"snapshot_digest"},
            )
        }
    )
    plan = original.model_copy(
        update={
            "runtime_profile": profile,
            "snapshot": snapshot,
            "plan_digest": ZERO_DIGEST,
        }
    )
    return plan.model_copy(
        update={
            "plan_digest": canonical_digest(
                plan,
                exclude={"plan_digest"},
            )
        }
    )


def _runtime_descriptor() -> dict[str, Any]:
    return {
        "schema_version": "abyss_stack_agent_os_runtime_profile_v1",
        "profile_id": "runtime-profile:abyss-stack-governed-execution-v1",
        "runtime_owner": "abyss-stack",
        "adapter_id": ABYSS_STACK_ADAPTER_VERSION,
        "adapter_protocol_version": "aoa_runtime_adapter_v1",
        "source_ref": ABYSS_STACK_ADAPTER_VERSION,
        "schema_ref": (
            "mechanics/governed-execution/parts/agent-os-adapter/"
            "schemas/agent-os-runtime-profile.schema.json"
        ),
        "supported_plan_schema_versions": ["aoa_control_plane_v1"],
        "supported_event_schema_versions": ["aoa_control_plane_v1"],
        "supported_effect_classes": ["read_only", "repo_mutation"],
        "required_constraint_artifacts": [
            {
                "owner_repo": "abyss-stack",
                "artifact_ref": "config/runtime-policy.yaml",
                "source_ref": "runtime-policy-v1",
                "schema_ref": "docs/runtime-policy.md",
                "schema_version": "v1",
            }
        ],
        "compatibility": [{"scenario_id": "bounded_change_safe"}],
        "boundaries": {"executes_through_governed_runner_only": True},
    }


def test_profile_loader_hashes_the_exact_owner_artifacts(
    tmp_path: Path,
) -> None:
    descriptor_path = tmp_path / "runtime-profile.v1.json"
    descriptor_path.write_text(
        json.dumps(_runtime_descriptor()) + "\n",
        encoding="utf-8",
    )
    policy_path = tmp_path / "runtime-policy.yaml"
    policy_path.write_text("enabled: true\n", encoding="utf-8")

    profile = load_abyss_stack_runtime_profile(
        descriptor_path,
        constraint_locations=(
            RuntimeArtifactLocation(
                owner_repo="abyss-stack",
                artifact_ref="config/runtime-policy.yaml",
                local_path=str(policy_path),
            ),
        ),
    )

    assert profile.provenance.artifact_digest == _digest(
        descriptor_path.read_text(encoding="utf-8")
    )
    assert profile.constraint_refs[0].artifact_digest == _digest(
        policy_path.read_text(encoding="utf-8")
    )
    assert profile.constraint_refs[0].source_ref == "runtime-policy-v1"


def test_profile_loader_rejects_incomplete_constraint_delivery(
    tmp_path: Path,
) -> None:
    descriptor_path = tmp_path / "runtime-profile.v1.json"
    descriptor_path.write_text(
        json.dumps(_runtime_descriptor()) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        AbyssStackAdapterError,
        match="constraint locations are incomplete",
    ):
        load_abyss_stack_runtime_profile(
            descriptor_path,
            constraint_locations=(),
        )


def _binding(plan: RunPlan) -> AbyssStackRuntimeBinding:
    request_ref = plan.scenario_binding.input_refs[0]
    request_path = "/tmp/aoa-agent-os/request.json"
    locations = tuple(
        RuntimeArtifactLocation(
            owner_repo=item.owner_repo,
            artifact_ref=item.artifact_ref,
            local_path=(
                request_path
                if item == request_ref
                else f"/tmp/aoa-agent-os/source-{index}.json"
            ),
        )
        for index, item in enumerate(plan.snapshot.source_refs)
    )
    return AbyssStackRuntimeBinding(
        binding_id="binding:test-bounded-change",
        plan_digest=plan.plan_digest,
        scenario_id=plan.scenario_binding.scenario.scenario_id,
        playbook_id="AOA-P-0011",
        request_ref=request_ref,
        request_path=request_path,
        source_locations=locations,
        abi_locations=tuple(
            RuntimeABILocation(
                owner_repo=item.owner_repo,
                abi_id=item.abi_id,
                local_path=f"/tmp/aoa-agent-os/abi-{index}.json",
            )
            for index, item in enumerate(plan.snapshot.abi_refs)
        ),
        adapter_contract_ref=plan.runtime_profile.provenance,
    )


class ReferenceTransport:
    def __init__(self, profile: RuntimeProfile) -> None:
        self.runtime = DeterministicReferenceAdapter(
            profile=profile,
            clock=lambda: NOW,
        )
        self.operations: list[str] = []

    def invoke(self, operation: str, payload: dict[str, Any]) -> Any:
        self.operations.append(operation)
        plan = RunPlan.model_validate(payload["plan"])
        from aoa_sdk.contracts.control_plane import SessionHandle

        session = SessionHandle.model_validate(payload["session"])
        if operation == "observe_snapshot":
            result = self.runtime.observe_snapshot(plan, session)
        elif operation == "dispatch":
            command = TypeAdapter(RuntimeCommand).validate_python(payload["command"])
            result = self.runtime.dispatch(plan, session, command)
        elif operation == "approval_requests":
            result = tuple(self.runtime.approval_requests(session))
        elif operation == "approval_decisions":
            result = tuple(self.runtime.approval_decisions(session))
        elif operation == "command_receipts":
            result = tuple(self.runtime.command_receipts(session))
        elif operation == "apply_approval":
            result = self.runtime.apply_approval(
                plan,
                session,
                ApprovalDecision.model_validate(payload["approval"]),
            )
        elif operation == "status":
            result = self.runtime.status(session)
        elif operation == "events":
            result = tuple(
                self.runtime.events(
                    session,
                    after_sequence=int(payload["after_sequence"]),
                )
            )
        elif operation == "outcome":
            result = self.runtime.outcome(session)
        else:
            raise AssertionError(f"unexpected operation: {operation}")
        if result is None:
            return None
        if isinstance(result, tuple):
            return [item.model_dump(mode="json") for item in result]
        return result.model_dump(mode="json")


def test_exact_binding_delegates_runner_lifecycle_through_transport() -> None:
    plan = _stack_plan()
    binding = _binding(plan)
    transport = ReferenceTransport(plan.runtime_profile)
    adapter = AbyssStackRuntimeAdapter(
        profile=plan.runtime_profile,
        binding=binding,
        transport=transport,
    )
    runner = AoARunner(clock=lambda: NOW, id_factory=lambda: "stack-transport")
    session = runner.prepare(plan)
    command = StartCommand(
        command_id="command:start",
        idempotency_key="key:start",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=plan.plan_digest,
        expected_revision=0,
        issued_at=NOW + timedelta(seconds=1),
        issued_by=session.prepared_by,
        reason="exercise the explicit production transport client",
    )

    assert runner.start(session, adapter, command).state == "awaiting_approval"
    request = runner.approval_requests(session)[0]
    decision = ApprovalDecision(
        decision_id="decision:approved",
        request_id=request.request_id,
        requirement_id=request.requirement_id,
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=plan.plan_digest,
        snapshot_digest=plan.snapshot.snapshot_digest,
        verdict="approved",
        approval_authority=request.approval_authority,
        decided_by=request.approval_authority,
        decided_at=NOW + timedelta(seconds=2),
        reason="approved for the transport contract test",
    )
    assert runner.approve(session, decision).state == "running"
    assert adapter.executes_plan_steps is True
    assert adapter.execution_owner == "abyss-stack"
    assert "observe_snapshot" in transport.operations
    assert "dispatch" in transport.operations
    assert "command_receipts" in transport.operations


def test_binding_rejects_a_missing_snapshot_location_before_transport() -> None:
    plan = _stack_plan()
    binding = _binding(plan).model_copy(
        update={"source_locations": _binding(plan).source_locations[:-1]}
    )
    with pytest.raises(
        AbyssStackAdapterError,
        match="do not cover the exact plan snapshot",
    ):
        assert_abyss_stack_binding_matches_plan(
            binding,
            plan,
            plan.runtime_profile,
        )


def test_subprocess_transport_uses_exact_argv_and_typed_envelope(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "bridge"
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        "print(json.dumps({\n"
        "  'schema_version': 'abyss_stack_agent_os_bridge_response_v1',\n"
        "  'ok': True,\n"
        "  'result': {\n"
        "    'operation': sys.argv[1],\n"
        "    'state_root': sys.argv[3],\n"
        "    'payload': payload,\n"
        "  },\n"
        "}))\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    state_root = tmp_path / "state"
    transport = AbyssStackSubprocessTransport(
        executable,
        state_root=state_root,
    )

    assert transport.invoke("status", {"sentinel": "exact"}) == {
        "operation": "status",
        "state_root": str(state_root),
        "payload": {"sentinel": "exact"},
    }


def test_subprocess_transport_isolates_an_explicit_python_interpreter(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "bridge.py"
    executable.write_text(
        "import json, os, sys\n"
        "print(json.dumps({\n"
        "  'schema_version': 'abyss_stack_agent_os_bridge_response_v1',\n"
        "  'ok': True,\n"
        "  'result': {\n"
        "    'isolated': sys.flags.isolated,\n"
        "    'pythonpath': os.environ.get('PYTHONPATH'),\n"
        "    'operation': sys.argv[1],\n"
        "  },\n"
        "}))\n",
        encoding="utf-8",
    )
    transport = AbyssStackSubprocessTransport(
        executable,
        state_root=tmp_path / "state",
        python_interpreter=sys.executable,
        environment={
            **os.environ,
            "PYTHONPATH": str(tmp_path / "spoofed-sdk"),
        },
    )

    assert transport.invoke("status", {}) == {
        "isolated": 1,
        "pythonpath": str(tmp_path / "spoofed-sdk"),
        "operation": "status",
    }


def test_subprocess_transport_rejects_relative_python_interpreter(
    tmp_path: Path,
) -> None:
    with pytest.raises(AbyssStackTransportError, match="interpreter.*absolute"):
        AbyssStackSubprocessTransport(
            tmp_path / "bridge.py",
            state_root=tmp_path / "state",
            python_interpreter="python3",
        )


def test_subprocess_transport_rejects_unversioned_output(tmp_path: Path) -> None:
    executable = tmp_path / "bridge"
    executable.write_text(
        "#!/usr/bin/env python3\nprint('{\"ok\": true, \"result\": {}}')\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    transport = AbyssStackSubprocessTransport(
        executable,
        state_root=tmp_path / "state",
    )

    with pytest.raises(AbyssStackTransportError, match="version"):
        transport.invoke("status", {})
