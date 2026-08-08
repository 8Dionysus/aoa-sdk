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
from ..contracts.admission_keeper import (
    AdmissionEvidenceNode,
    AdmissionKeeperSpec,
    AdmissionKeeperState,
)
from ..contracts.organ_registry_v2 import (
    OrganContourSupplement,
    OrganRegistryRuntimeOverlay,
)
from ..contracts.organ_orchestration import (
    CrossOrganOrchestrationRequest,
    CrossOrganOrchestrationRun,
    CrossOrganStageObservation,
)
from ..organs import (
    AdmissionKeeperError,
    KeeperEvidenceStore,
    apply_contour_supplement,
    apply_registry_runtime_overlay,
    OrganAdmissionError,
    OrganOrchestrationError,
    OrganRegistryError,
    OrgansAPI,
    compile_registry,
    compile_registry_v2,
    build_keeper_state,
    load_registry_source,
    load_registry_source_v2,
    materialize_admission_decision,
    materialize_admission_evidence,
    materialize_keeper_spec,
    migrate_registry_file_v1_to_v2,
    plan_keeper_refresh,
    run_keeper_cycle,
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
            "plan_id": payload.get("plan_id"),
            "state_id": payload.get("state_id"),
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


@organs_app.command("registry-v2-validate")
def organs_registry_v2_validate(
    registry: str = typer.Argument(..., help="Explicit contour-addressed registry JSON."),
) -> None:
    try:
        source = load_registry_source_v2(registry)
        projection = compile_registry_v2(source)
    except (OrganRegistryError, ValidationError) as exc:
        _fail(exc)
    _emit(
        {
            "valid": True,
            "registry_id": source.registry_id,
            "organ_count": len(source.records),
            "contour_count": len(projection.entries),
            "source_digest": projection.source_digest,
            "projection_digest": projection.projection_digest,
            "registry_mutation_performed": False,
        }
    )


@organs_app.command("registry-migrate-v2")
def organs_registry_migrate_v2(
    registry: str = typer.Argument(..., help="Existing v1 registry JSON."),
    migration_decision_ref: str = typer.Option(
        ...,
        "--migration-decision-ref",
        help="Owner-reviewed decision authorizing only the shape migration.",
    ),
    output: str | None = typer.Option(None, "--output"),
    runtime_overlay: str | None = typer.Option(
        None,
        "--runtime-overlay",
        help="Owner-reviewed exact runtime bindings; does not refresh admission.",
    ),
    contour_supplement: list[str] | None = typer.Option(
        None,
        "--contour-supplement",
        help="Owner supplement adding only new shadow contour shapes; repeatable.",
    ),
) -> None:
    try:
        migrated = migrate_registry_file_v1_to_v2(
            registry,
            migration_decision_ref=migration_decision_ref,
        )
        for supplement_path in contour_supplement or []:
            supplement = OrganContourSupplement.model_validate_json(
                Path(supplement_path).read_bytes()
            )
            migrated = apply_contour_supplement(migrated, supplement)
        if runtime_overlay is not None:
            overlay = OrganRegistryRuntimeOverlay.model_validate_json(
                Path(runtime_overlay).read_bytes()
            )
            migrated = apply_registry_runtime_overlay(migrated, overlay)
        compile_registry_v2(migrated)
    except (OrganRegistryError, ValidationError) as exc:
        _fail(exc)
    _write_or_emit(migrated, output)


def _load_keeper_nodes(path: str | None) -> tuple[AdmissionEvidenceNode, ...]:
    if path is None:
        return ()
    root = Path(path).expanduser().resolve(strict=False)
    if not root.is_dir() or root.is_symlink():
        raise OSError("keeper node path must be a non-symlink directory")
    return tuple(
        AdmissionEvidenceNode.model_validate_json(candidate.read_bytes())
        for candidate in sorted(root.glob("*.json"))
        if candidate.is_file() and not candidate.is_symlink()
    )


@organs_app.command("keeper-plan")
def organs_keeper_plan(
    spec_path: str = typer.Argument(..., help="Admission Keeper spec JSON."),
    nodes: str | None = typer.Option(None, "--nodes"),
    prior_state: str | None = typer.Option(None, "--prior-state"),
    renewal_margin_seconds: int = typer.Option(60, "--renewal-margin-seconds"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        spec = materialize_keeper_spec(
            AdmissionKeeperSpec.model_validate_json(Path(spec_path).read_bytes())
        )
        prior = (
            AdmissionKeeperState.model_validate_json(Path(prior_state).read_bytes())
            if prior_state is not None
            else None
        )
        result = plan_keeper_refresh(
            spec,
            nodes=_load_keeper_nodes(nodes),
            prior_state=prior,
            renewal_margin_seconds=renewal_margin_seconds,
        )
    except (OSError, AdmissionKeeperError, ValidationError) as exc:
        _fail(exc)
    _write_or_emit(result, output)


@organs_app.command("keeper-state")
def organs_keeper_state(
    spec_path: str = typer.Argument(..., help="Admission Keeper spec JSON."),
    nodes: str = typer.Option(..., "--nodes"),
    prior_state: str | None = typer.Option(None, "--prior-state"),
    last_good_ref: str | None = typer.Option(None, "--last-good-ref"),
    last_good_digest: str | None = typer.Option(None, "--last-good-digest"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    try:
        spec = materialize_keeper_spec(
            AdmissionKeeperSpec.model_validate_json(Path(spec_path).read_bytes())
        )
        prior = (
            AdmissionKeeperState.model_validate_json(Path(prior_state).read_bytes())
            if prior_state is not None
            else None
        )
        result = build_keeper_state(
            spec,
            nodes=_load_keeper_nodes(nodes),
            prior_state=prior,
            last_good_state_ref=last_good_ref,
            last_good_state_digest=last_good_digest,
        )
    except (OSError, AdmissionKeeperError, ValidationError) as exc:
        _fail(exc)
    _write_or_emit(result, output)


@organs_app.command("keeper-cycle")
def organs_keeper_cycle(
    spec_path: str = typer.Argument(..., help="Admission Keeper spec JSON."),
    store_root: str = typer.Option(..., "--store-root"),
    inbox: str | None = typer.Option(None, "--inbox"),
    renewal_margin_seconds: int = typer.Option(60, "--renewal-margin-seconds"),
) -> None:
    try:
        spec = AdmissionKeeperSpec.model_validate_json(Path(spec_path).read_bytes())
        inbox_paths: tuple[Path, ...] = ()
        if inbox is not None:
            inbox_root = Path(inbox).expanduser().resolve(strict=False)
            if inbox_root.is_symlink() or not inbox_root.is_dir():
                raise OSError("keeper inbox must be a non-symlink directory")
            inbox_paths = tuple(sorted(inbox_root.glob("*.json")))
        result = run_keeper_cycle(
            spec,
            store=KeeperEvidenceStore(store_root),
            inbox_paths=inbox_paths,
            renewal_margin_seconds=renewal_margin_seconds,
        )
    except (OSError, AdmissionKeeperError, ValidationError) as exc:
        _fail(exc)
    _emit(result)


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
