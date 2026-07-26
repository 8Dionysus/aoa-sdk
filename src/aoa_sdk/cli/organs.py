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
    PolicyFamily,
)
from ..organs import OrganRegistryError, OrgansAPI, compile_registry, load_registry_source
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
