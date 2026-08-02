from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from pydantic import TypeAdapter, ValidationError

from ..contracts.organs import (
    ActivationRequest,
    EffectClass,
    FreshnessState,
    OrganRecord,
    PolicyFamily,
)
from ..contracts.organ_admission import (
    AdmissionDecisionReceipt,
    AdmissionDecisionStatement,
    AdmissionEvidenceReceipt,
    AdmissionEvidenceStatement,
    OrganAdmissionCandidate,
    OrganAdmissionRequest,
    OrganAdmissionRun,
)
from ..contracts.organ_orchestration import (
    CrossOrganOrchestrationRequest,
    CrossOrganOrchestrationRun,
    CrossOrganStageObservation,
)
from ..organs import (
    OrganAdmissionError,
    OrganOrchestrationError,
    OrganRegistryError,
    OrgansAPI,
    compile_registry,
    load_registry_source,
    materialize_admission_decision,
    materialize_admission_evidence,
)
from ..workspace.discovery import Workspace


organs_app = typer.Typer(
    help="Inspect an explicit owner-bounded organ registry and compile candidate plans"
)


def _api(root: str, registry: str | None) -> OrgansAPI:
    return OrgansAPI(Workspace.discover(root), registry_path=registry)


def _emit(value: Any) -> None:
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True))


def _fail(exc: Exception) -> None:
    typer.echo(f"error: {exc}", err=True)
    raise typer.Exit(code=1) from exc


def _write_or_emit(value: Any, output: str | None) -> None:
    if output is None:
        _emit(value)
        return
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    rendered = json.dumps(
        payload,
        indent=2,
        ensure_ascii=True,
        sort_keys=True,
    )
    destination = Path(output).expanduser().resolve(strict=False)
    destination.write_text(rendered + "\n", encoding="utf-8")
    _emit(
        {
            "written": str(destination),
            "snapshot_digest": payload.get("snapshot_digest"),
            "candidate_id": payload.get("candidate_id"),
            "authorization_id": payload.get("authorization_id"),
            "evidence_id": payload.get("evidence_id"),
            "decision_id": payload.get("decision_id"),
            "owner_tools_executed_by_sdk": False,
        }
    )


@organs_app.command("validate")
def organs_validate(
    registry: str = typer.Argument(..., help="Explicit private registry source JSON."),
) -> None:
    try:
        source = load_registry_source(registry)
        projection = compile_registry(source)
    except (OrganRegistryError, ValidationError) as exc:
        _fail(exc)
    _emit(
        {
            "valid": True,
            "registry_id": source.registry_id,
            "record_count": len(source.records),
            "source_digest": projection.source_digest,
            "projection_digest": projection.projection_digest,
            "execution_authorized": False,
        }
    )


@organs_app.command("compile")
def organs_compile(
    registry: str = typer.Argument(..., help="Explicit private registry source JSON."),
    output: str | None = typer.Option(
        None,
        "--output",
        help="Explicit path for the secret-free projection; omit to print only.",
    ),
) -> None:
    try:
        projection = compile_registry(load_registry_source(registry))
    except (OrganRegistryError, ValidationError) as exc:
        _fail(exc)
    rendered = json.dumps(
        projection.model_dump(mode="json"),
        indent=2,
        ensure_ascii=True,
        sort_keys=True,
    )
    if output is None:
        typer.echo(rendered)
        return
    destination = Path(output).expanduser().resolve(strict=False)
    destination.write_text(rendered + "\n", encoding="utf-8")
    _emit(
        {
            "written": str(destination),
            "projection_digest": projection.projection_digest,
            "execution_authorized": False,
        }
    )


@organs_app.command("catalog")
def organs_catalog(
    root: str = typer.Option(".", "--root"),
    registry: str | None = typer.Option(None, "--registry"),
    query: str | None = typer.Option(None, "--query"),
    source_owner: str | None = typer.Option(None, "--source-owner"),
    maximum_policy: str = typer.Option("read", "--maximum-policy"),
    freshness_state: list[str] | None = typer.Option(None, "--freshness-state"),
    effect_class: list[str] | None = typer.Option(None, "--effect-class"),
    allow_organ: list[str] | None = typer.Option(None, "--allow-organ"),
    allow_capability: list[str] | None = typer.Option(
        None,
        "--allow-capability",
    ),
    max_results: int = typer.Option(24, "--max-results"),
    byte_budget: int = typer.Option(32_768, "--byte-budget"),
) -> None:
    try:
        policy: PolicyFamily = TypeAdapter(PolicyFamily).validate_python(
            maximum_policy
        )
        freshness: tuple[FreshnessState, ...] | None = (
            TypeAdapter(tuple[FreshnessState, ...]).validate_python(
                freshness_state
            )
            if freshness_state
            else None
        )
        effects: tuple[EffectClass, ...] | None = (
            TypeAdapter(tuple[EffectClass, ...]).validate_python(effect_class)
            if effect_class
            else None
        )
        result = _api(root, registry).catalog(
            query=query,
            source_owner=source_owner,
            maximum_policy=policy,
            freshness_states=freshness,
            effect_classes=effects,
            allowed_organ_ids=tuple(allow_organ) if allow_organ else None,
            allowed_capability_ids=(
                tuple(allow_capability) if allow_capability else None
            ),
            max_results=max_results,
            byte_budget=byte_budget,
        )
    except (OrganRegistryError, ValidationError) as exc:
        _fail(exc)
    _emit(result)


@organs_app.command("inspect")
def organs_inspect(
    organ_id: str = typer.Argument(...),
    root: str = typer.Option(".", "--root"),
    registry: str | None = typer.Option(None, "--registry"),
) -> None:
    try:
        result = _api(root, registry).inspect_organ(organ_id)
    except (OrganRegistryError, ValidationError) as exc:
        _fail(exc)
    _emit(result)


@organs_app.command("capability")
def organs_capability(
    organ_id: str = typer.Argument(...),
    capability_id: str = typer.Argument(...),
    root: str = typer.Option(".", "--root"),
    registry: str | None = typer.Option(None, "--registry"),
) -> None:
    try:
        result = _api(root, registry).inspect_capability(organ_id, capability_id)
    except (OrganRegistryError, ValidationError) as exc:
        _fail(exc)
    _emit(result)


@organs_app.command("plan")
def organs_plan(
    request: str = typer.Argument(..., help="Activation request JSON path."),
    root: str = typer.Option(".", "--root"),
    registry: str | None = typer.Option(None, "--registry"),
) -> None:
    try:
        payload = json.loads(Path(request).read_text(encoding="utf-8"))
        plan = _api(root, registry).compile_activation(
            ActivationRequest.model_validate(payload)
        )
    except (
        OSError,
        json.JSONDecodeError,
        OrganRegistryError,
        ValidationError,
    ) as exc:
        _fail(exc)
    _emit(plan)


@organs_app.command("admission-address-evidence")
def organs_admission_address_evidence(
    statement: str = typer.Argument(
        ...,
        help="Externally issued admission evidence statement JSON path.",
    ),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        payload = json.loads(Path(statement).read_text(encoding="utf-8"))
        receipt = materialize_admission_evidence(
            AdmissionEvidenceStatement.model_validate(payload)
        )
    except (OSError, json.JSONDecodeError, OrganAdmissionError, ValidationError) as exc:
        _fail(exc)
    _write_or_emit(receipt, output)


@organs_app.command("admission-audit")
def organs_admission_audit(
    organ_id: str = typer.Argument(...),
    capability_id: str = typer.Argument(...),
    root: str = typer.Option(".", "--root"),
    registry: str | None = typer.Option(None, "--registry"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        audit = _api(root, registry).audit_admission_baseline(
            organ_id,
            capability_id,
        )
    except (OrganAdmissionError, OrganRegistryError, ValidationError) as exc:
        _fail(exc)
    _write_or_emit(audit, output)


@organs_app.command("admission-start")
def organs_admission_start(
    request: str = typer.Argument(..., help="Admission request JSON path."),
    root: str = typer.Option(".", "--root"),
    registry: str | None = typer.Option(None, "--registry"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        payload = json.loads(Path(request).read_text(encoding="utf-8"))
        run = _api(root, registry).start_admission(
            OrganAdmissionRequest.model_validate(payload)
        )
    except (
        OSError,
        json.JSONDecodeError,
        OrganAdmissionError,
        OrganRegistryError,
        ValidationError,
    ) as exc:
        _fail(exc)
    _write_or_emit(run, output)


@organs_app.command("admission-advance")
def organs_admission_advance(
    run_path: str = typer.Argument(..., help="Current admission run JSON path."),
    evidence: str = typer.Argument(..., help="Admission evidence receipt JSON path."),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        run_payload = json.loads(Path(run_path).read_text(encoding="utf-8"))
        evidence_payload = json.loads(Path(evidence).read_text(encoding="utf-8"))
        run = OrgansAPI.advance_admission(
            OrganAdmissionRun.model_validate(run_payload),
            AdmissionEvidenceReceipt.model_validate(evidence_payload),
        )
    except (OSError, json.JSONDecodeError, OrganAdmissionError, ValidationError) as exc:
        _fail(exc)
    _write_or_emit(run, output)


@organs_app.command("admission-validate")
def organs_admission_validate(
    run_path: str = typer.Argument(..., help="Admission run JSON path."),
) -> None:
    try:
        payload = json.loads(Path(run_path).read_text(encoding="utf-8"))
        run = OrgansAPI.validate_admission(
            OrganAdmissionRun.model_validate(payload)
        )
    except (OSError, json.JSONDecodeError, OrganAdmissionError, ValidationError) as exc:
        _fail(exc)
    _emit(
        {
            "valid": True,
            "run_id": run.run_id,
            "snapshot_digest": run.snapshot_digest,
            "state": run.state,
            "next_stage": run.next_stage,
            "next_owner": run.next_owner,
            "registry_mutated_by_sdk": False,
            "central_proof_computed_by_sdk": False,
            "owner_acceptance_inferred_by_sdk": False,
        }
    )


@organs_app.command("admission-candidate")
def organs_admission_candidate(
    run_path: str = typer.Argument(..., help="Complete admission run JSON path."),
    root: str = typer.Option(".", "--root"),
    registry: str | None = typer.Option(None, "--registry"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        payload = json.loads(Path(run_path).read_text(encoding="utf-8"))
        candidate = _api(root, registry).build_admission_candidate(
            OrganAdmissionRun.model_validate(payload)
        )
    except (
        OSError,
        json.JSONDecodeError,
        OrganAdmissionError,
        OrganRegistryError,
        ValidationError,
    ) as exc:
        _fail(exc)
    _write_or_emit(candidate, output)


@organs_app.command("admission-address-decision")
def organs_admission_address_decision(
    statement: str = typer.Argument(
        ...,
        help="Externally issued owner/operator decision statement JSON path.",
    ),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        payload = json.loads(Path(statement).read_text(encoding="utf-8"))
        receipt = materialize_admission_decision(
            AdmissionDecisionStatement.model_validate(payload)
        )
    except (OSError, json.JSONDecodeError, OrganAdmissionError, ValidationError) as exc:
        _fail(exc)
    _write_or_emit(receipt, output)


@organs_app.command("admission-authorize")
def organs_admission_authorize(
    run_path: str = typer.Argument(..., help="Complete admission run JSON path."),
    candidate_path: str = typer.Argument(..., help="Admission candidate JSON path."),
    owner_decision_path: str = typer.Argument(..., help="Owner decision receipt path."),
    operator_decision_path: str = typer.Argument(
        ...,
        help="Operator decision receipt path.",
    ),
    target_record_path: str = typer.Argument(
        ...,
        help="Exact admitted target OrganRecord JSON path.",
    ),
    root: str = typer.Option(".", "--root"),
    registry: str | None = typer.Option(None, "--registry"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        run = OrganAdmissionRun.model_validate(
            json.loads(Path(run_path).read_text(encoding="utf-8"))
        )
        candidate = OrganAdmissionCandidate.model_validate(
            json.loads(Path(candidate_path).read_text(encoding="utf-8"))
        )
        owner_decision = AdmissionDecisionReceipt.model_validate(
            json.loads(Path(owner_decision_path).read_text(encoding="utf-8"))
        )
        operator_decision = AdmissionDecisionReceipt.model_validate(
            json.loads(Path(operator_decision_path).read_text(encoding="utf-8"))
        )
        target_record = OrganRecord.model_validate(
            json.loads(Path(target_record_path).read_text(encoding="utf-8"))
        )
        authorization = _api(root, registry).authorize_registry_transition(
            run,
            candidate,
            owner_decision,
            operator_decision,
            target_record,
        )
    except (
        OSError,
        json.JSONDecodeError,
        OrganAdmissionError,
        OrganRegistryError,
        ValidationError,
    ) as exc:
        _fail(exc)
    _write_or_emit(authorization, output)


@organs_app.command("orchestration-start")
def organs_orchestration_start(
    request: str = typer.Argument(
        ...,
        help="Pinned cross-organ orchestration request JSON path.",
    ),
    root: str = typer.Option(".", "--root"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        payload = json.loads(Path(request).read_text(encoding="utf-8"))
        run = _api(root, None).start_orchestration(
            CrossOrganOrchestrationRequest.model_validate(payload)
        )
    except (
        OSError,
        json.JSONDecodeError,
        OrganOrchestrationError,
        ValidationError,
    ) as exc:
        _fail(exc)
    _write_or_emit(run, output)


@organs_app.command("orchestration-advance")
def organs_orchestration_advance(
    run_path: str = typer.Argument(..., help="Current orchestration run JSON path."),
    observation: str = typer.Argument(
        ...,
        help="One host-receipted owner stage observation JSON path.",
    ),
    root: str = typer.Option(".", "--root"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        run_payload = json.loads(Path(run_path).read_text(encoding="utf-8"))
        observation_payload = json.loads(
            Path(observation).read_text(encoding="utf-8")
        )
        updated = _api(root, None).advance_orchestration(
            CrossOrganOrchestrationRun.model_validate(run_payload),
            CrossOrganStageObservation.model_validate(observation_payload),
        )
    except (
        OSError,
        json.JSONDecodeError,
        OrganOrchestrationError,
        ValidationError,
    ) as exc:
        _fail(exc)
    _write_or_emit(updated, output)


@organs_app.command("orchestration-validate")
def organs_orchestration_validate(
    run_path: str = typer.Argument(..., help="Orchestration run JSON path."),
    root: str = typer.Option(".", "--root"),
) -> None:
    try:
        payload = json.loads(Path(run_path).read_text(encoding="utf-8"))
        run = _api(root, None).validate_orchestration(
            CrossOrganOrchestrationRun.model_validate(payload)
        )
    except (
        OSError,
        json.JSONDecodeError,
        OrganOrchestrationError,
        ValidationError,
    ) as exc:
        _fail(exc)
    _emit(
        {
            "valid": True,
            "run_id": run.run_id,
            "snapshot_digest": run.snapshot_digest,
            "state": run.state,
            "stage_count": len(run.stages),
            "next_stage_kind": run.next_stage_kind,
            "next_owner": run.next_owner,
            "owner_tools_executed_by_sdk": False,
            "proof_computed_by_sdk": False,
            "durable_memory_written_by_sdk": False,
            "acceptance_inferred_by_sdk": False,
        }
    )
