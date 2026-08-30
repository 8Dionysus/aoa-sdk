from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from aoa_sdk.contracts.control_plane import ContentRef, ProvenanceRef
from aoa_sdk.contracts.delegation import (
    BoundedImmutableInput,
    DelegationAdapterProfile,
    DelegationEnvelope,
    DelegationLifecycleRefs,
    EphemeralReadWorkerV1,
    ExternalIncarnationV1,
    validate_delegation_class,
)


ZERO_DIGEST = "sha256:" + "0" * 64
ROOT = Path(__file__).resolve().parents[5]
SCHEMA_PATH = (
    ROOT
    / "mechanics/boundary-bridge/parts/agent-incarnation-binding/schemas"
    / "delegation-classes.schema.json"
)


def _ref(owner_repo: str, artifact_ref: str, schema_version: str = "fixture-v1") -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner_repo,
        artifact_ref=artifact_ref,
        source_ref="fixture-source",
        artifact_digest=ZERO_DIGEST,
        schema_ref="schemas/fixture.schema.json",
        schema_version=schema_version,
    )


def _content(owner_repo: str, object_id: str, schema_version: str) -> ContentRef:
    return ContentRef(
        object_id=object_id,
        owner_repo=owner_repo,
        schema_version=schema_version,
        digest=ZERO_DIGEST,
    )


def _adapter(kind: str, delegation_class: str) -> DelegationAdapterProfile:
    return DelegationAdapterProfile(
        adapter_id=f"fixture-{kind}-{delegation_class}",
        adapter_kind=kind,
        delegation_class=delegation_class,
        implementation_ref=_ref("abyss-stack", "fixture/adapter.json"),
    )


def _common(delegation_class: str, adapter: DelegationAdapterProfile) -> dict[str, object]:
    return {
        "delegation_id": "delegation:fixture",
        "correlation_id": "correlation:fixture",
        "delegation_class": delegation_class,
        "parent_holder_ref": _content("aoa-agents", "holder:parent", "holder-v1"),
        "adapter": adapter,
        "economy_observation_ref": _content(
            "abyss-stack",
            "observation:fixture",
            "abyss_delegation_economy_observation_v1",
        ),
        "provenance": _ref("aoa-sdk", "delegation/fixture.json"),
    }


def _ephemeral() -> EphemeralReadWorkerV1:
    payload = _common(
        "ephemeral_read_worker_v1",
        _adapter("local_provider", "ephemeral_read_worker_v1"),
    )
    payload.update(
        {
            "input": BoundedImmutableInput(
                input_refs=(_ref("aoa-agents", "fixture/input.json"),),
                snapshot_digest=ZERO_DIGEST,
                max_input_bytes=4096,
                max_output_bytes=128,
            ),
            "result_ref": _content(
                "abyss-stack", "result:fixture", "abyss_ephemeral_read_result_v1"
            ),
        }
    )
    return EphemeralReadWorkerV1.model_validate(payload)


def _external() -> ExternalIncarnationV1:
    payload = _common(
        "external_incarnation_v1",
        _adapter("codex_cli", "external_incarnation_v1"),
    )
    payload.update(
        {
            "role_contract_ref": _ref("aoa-agents", "agents/roles/architect/profile.json"),
            "actor_mandate_ref": _content(
                "aoa-agents", "mandate:fixture", "actor-mandate-v1"
            ),
            "model_realization_ref": _ref(
                "aoa-models", "source/realizations/fixture.json", "aoa_model_realization_v1"
            ),
            "incarnation_binding_ref": _content(
                "aoa-sdk", "binding:fixture", "aoa_agent_incarnation_binding_v2"
            ),
            "continuation_ref": _content(
                "aoa-sdk", "continuation:fixture", "aoa_continuation_obligation_v1"
            ),
            "runtime_process_ref": _content(
                "abyss-stack", "process:fixture", "abyss_external_incarnation_process_v1"
            ),
            "runtime_session_ref": _content(
                "abyss-stack", "session:fixture", "abyss_external_incarnation_session_v1"
            ),
            "runtime_event_refs": (
                _content(
                    "abyss-stack", "event:fixture:1", "abyss_external_incarnation_event_v1"
                ),
                _content(
                    "abyss-stack", "event:fixture:2", "abyss_external_incarnation_event_v1"
                ),
            ),
            "responsibility_transfer_ref": _content(
                "aoa-agents", "transfer:fixture", "responsibility-transfer-v1"
            ),
            "reviewed_return_ref": _content(
                "aoa-agents",
                "return:fixture",
                "responsibility-return-disposition-v1",
            ),
            "lifecycle": DelegationLifecycleRefs(
                eval_ref=_content("aoa-evals", "eval:fixture", "eval-verdict-v1"),
                closeout_ref=_content("goal-owner", "closeout:fixture", "closeout-v1"),
                acceptance_ref=_content(
                    "goal-owner", "acceptance:fixture", "acceptance-v1"
                ),
            ),
            "allowed_effect_classes": ("read_only", "repo_mutation"),
        }
    )
    return ExternalIncarnationV1.model_validate(payload)


def test_both_classes_are_explicit_and_discriminated() -> None:
    ephemeral = _ephemeral()
    external = _external()

    assert ephemeral.parent_retains_responsibility is True
    assert ephemeral.role_formation_allowed is False
    assert external.responsibility_transferred is True
    assert external.reviewed_return_required is True
    assert external.lifecycle.eval_ref is not None
    assert external.lifecycle.closeout_ref != external.lifecycle.acceptance_ref
    assert DelegationEnvelope.model_validate(ephemeral).root == ephemeral
    assert validate_delegation_class(external.model_dump()) == external


def test_adapter_abi_is_provider_neutral_but_adapter_ids_differ() -> None:
    codex = _adapter("codex_cli", "external_incarnation_v1")
    local = _adapter("local_provider", "external_incarnation_v1")

    assert codex.provider_neutral_abi is True
    assert local.provider_neutral_abi is True
    assert codex.schema_version == local.schema_version
    assert codex.adapter_id != local.adapter_id


def test_ephemeral_worker_rejects_codex_and_external_rejects_owner_drift() -> None:
    ephemeral_payload = _ephemeral().model_dump()
    ephemeral_payload["adapter"] = _adapter(
        "codex_cli", "ephemeral_read_worker_v1"
    ).model_dump()
    with pytest.raises(ValidationError, match="local-provider"):
        EphemeralReadWorkerV1.model_validate(ephemeral_payload)

    external_payload = _external().model_dump()
    external_payload["model_realization_ref"]["owner_repo"] = "aoa-agents"
    with pytest.raises(ValidationError, match="model realization"):
        ExternalIncarnationV1.model_validate(external_payload)


def test_external_lifecycle_evidence_cannot_collapse_into_one_ref() -> None:
    payload = _external().model_dump()
    payload["lifecycle"]["acceptance_ref"] = payload["lifecycle"]["closeout_ref"]

    with pytest.raises(ValidationError, match="remain distinct"):
        ExternalIncarnationV1.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "owner_repo", "schema_version", "message"),
    (
        ("eval_ref", "aoa-evals", "wrong-eval-v1", "eval_ref"),
        ("closeout_ref", "other-owner", "closeout-v1", "closeout_ref"),
        ("acceptance_ref", "goal-owner", "wrong-acceptance-v1", "acceptance_ref"),
    ),
)
def test_external_lifecycle_evidence_keeps_owner_and_schema(
    field: str, owner_repo: str, schema_version: str, message: str
) -> None:
    payload = _external().model_dump()
    payload["lifecycle"][field] = _content(
        owner_repo, f"{field}:fixture", schema_version
    ).model_dump()

    with pytest.raises(ValidationError, match=message):
        ExternalIncarnationV1.model_validate(payload)


def test_generated_schema_contains_the_two_class_discriminator() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    encoded = json.dumps(schema, sort_keys=True)
    assert "ephemeral_read_worker_v1" in encoded
    assert "external_incarnation_v1" in encoded
    assert schema["$id"] == "urn:aoa-sdk:delegation-classes:v1"
    assert schema["type"] == "object"
