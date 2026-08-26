from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from aoa_sdk.contracts.organ_exposure import ExposureSelectionRequest
from aoa_sdk.organs import OrgansAPI

from test_organ_access import NOW, _api, _record, _source


def _request(*, baseline_ready: bool, reveal_schemas: bool) -> ExposureSelectionRequest:
    return ExposureSelectionRequest(
        request_id="exposure-request-1",
        organ_id="aoa-kag",
        capability_id="knowledge-inspect",
        selected_primitive_ids=("inspect-knowledge",),
        requested_policy_family="read",
        requested_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        baseline_ready=baseline_ready,
        baseline_evidence=(
            {
                "owner": "d0-baseline",
                "evidence_ref": "receipt://d0/baseline-ready",
                "revision": "baseline-1",
                "observed_at": NOW.isoformat(),
                "expires_at": (NOW + timedelta(hours=1)).isoformat(),
            }
            if baseline_ready
            else None
        ),
        reveal_schemas=reveal_schemas,
        selection_reason="bounded disclosure fixture",
    )


def test_progressive_exposure_is_default_off_and_preserves_refusal_reasons(
    tmp_path,
) -> None:
    api = _api(tmp_path, _source(_record("aoa-kag", "admitted")))
    plan = api.compile_exposure(
        _request(baseline_ready=True, reveal_schemas=True),
        evaluated_at=NOW,
    )

    assert plan.plan_state == "blocked"
    assert plan.execution_authorized is False
    assert plan.activation_authorized is False
    assert plan.visible_tools == ()
    assert plan.rendered_snapshot.rendered_bytes == 2
    assert plan.rendered_snapshot.rendered_tokens is None
    assert "progressive_exposure_disabled" in plan.refusal_reasons
    assert "baseline_gate_satisfied" not in plan.expansion_reasons


def test_explicit_opt_in_reveals_ordered_tools_with_bounded_accounting(
    tmp_path,
) -> None:
    workspace_api = _api(tmp_path, _source(_record("aoa-kag", "admitted")))
    api = OrgansAPI(
        workspace_api.workspace,
        registry_path=workspace_api.registry_path,
        clock=lambda: NOW,
        progressive_exposure_enabled=True,
    )
    plan = api.compile_exposure(
        _request(baseline_ready=True, reveal_schemas=True),
        evaluated_at=NOW,
    )

    assert plan.plan_state == "candidate"
    assert plan.capability.qualified_capability_id == (
        "aoa-kag:aoa-kag:knowledge-inspect"
    )
    assert [tool.tool_id for tool in plan.visible_tools] == [
        "knowledge-inspect.inspect-knowledge"
    ]
    assert plan.rendered_snapshot.rendered_bytes > 2
    assert plan.rendered_snapshot.rendered_tokens is not None
    assert plan.rendered_snapshot.token_count_posture == "estimated"
    assert plan.rendered_snapshot.rendered_schema_digest.startswith("sha256:")
    assert plan.refusal_reasons == ()
    assert plan.expansion_reasons

    authorization = api.prepare_exposure_authorization(plan)
    assert authorization.authorization_state == "external_owner_required"
    assert authorization.activation_authorized is False
    assert authorization.execution_authorized is False
    assert authorization.visible_tool_ids == plan.rendered_snapshot.visible_tool_ids


def test_exposure_request_rejects_duplicate_ordered_selection() -> None:
    payload = _request(
        baseline_ready=False,
        reveal_schemas=False,
    ).model_dump(mode="json")
    payload["selected_primitive_ids"] = [
        "inspect-knowledge",
        "inspect-knowledge",
    ]
    with pytest.raises(ValidationError, match="unique and ordered"):
        ExposureSelectionRequest.model_validate(payload)


def test_exposure_rejects_unqualified_baseline_evidence(tmp_path) -> None:
    api = OrgansAPI(
        _api(tmp_path, _source(_record("aoa-kag", "admitted"))).workspace,
        registry_path=_api(tmp_path, _source(_record("aoa-kag", "admitted"))).registry_path,
        clock=lambda: NOW,
        progressive_exposure_enabled=True,
    )
    request = _request(baseline_ready=True, reveal_schemas=True).model_dump(mode="json")
    request["baseline_evidence"]["owner"] = "unrelated-owner"
    with pytest.raises(Exception, match="canonical d0 baseline-ready"):
        api.compile_exposure(
            ExposureSelectionRequest.model_validate(request),
            evaluated_at=NOW,
        )


def test_exposure_refuses_missing_owner_schema_digest(tmp_path) -> None:
    record = _record("aoa-kag", "admitted")
    record["endpoint"]["server_schema_digest"] = None
    source = _source(record)
    workspace_api = _api(tmp_path, source)
    api = OrgansAPI(
        workspace_api.workspace,
        registry_path=workspace_api.registry_path,
        clock=lambda: NOW,
        progressive_exposure_enabled=True,
    )
    with pytest.raises(Exception, match="owner-authored server schema digest"):
        api.compile_exposure(
            _request(baseline_ready=True, reveal_schemas=True),
            evaluated_at=NOW,
        )


def test_exposure_rejects_tampered_plan_identity(tmp_path) -> None:
    workspace_api = _api(tmp_path, _source(_record("aoa-kag", "admitted")))
    api = OrgansAPI(
        workspace_api.workspace,
        registry_path=workspace_api.registry_path,
        clock=lambda: NOW,
        progressive_exposure_enabled=True,
    )
    plan = api.compile_exposure(
        _request(baseline_ready=True, reveal_schemas=True),
        evaluated_at=NOW,
    )
    payload = plan.model_dump(mode="json")
    payload["expires_at"] = (NOW + timedelta(minutes=30)).isoformat()
    with pytest.raises(ValidationError, match="content addressed"):
        type(plan).model_validate(payload)


def test_exposure_rejects_mismatched_effect_approval(tmp_path) -> None:
    workspace_api = _api(tmp_path, _source(_record("aoa-kag", "admitted", effect=True)))
    api = OrgansAPI(
        workspace_api.workspace,
        registry_path=workspace_api.registry_path,
        clock=lambda: NOW,
        progressive_exposure_enabled=True,
    )
    request = ExposureSelectionRequest(
        request_id="effect-exposure-request",
        organ_id="aoa-kag",
        capability_id="knowledge-publish",
        selected_primitive_ids=("publish-change",),
        requested_policy_family="external_effect",
        requested_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        baseline_ready=True,
        baseline_evidence={
            "owner": "d0-baseline",
            "evidence_ref": "receipt://d0/baseline-ready",
            "revision": "baseline-1",
            "observed_at": NOW.isoformat(),
            "expires_at": (NOW + timedelta(hours=1)).isoformat(),
        },
        reveal_schemas=True,
        approval_ref={
            "owner": "wrong-owner",
            "evidence_ref": "approval://wrong",
            "revision": "approval-1",
            "observed_at": NOW.isoformat(),
            "expires_at": (NOW + timedelta(hours=1)).isoformat(),
        },
    )
    plan = api.compile_exposure(request, evaluated_at=NOW)
    assert plan.plan_state == "blocked"
    assert "approval_owner_mismatch" in plan.refusal_reasons
