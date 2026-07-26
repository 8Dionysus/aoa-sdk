"""CLI for C1 route resolution and explanation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError

from ..contracts.control_plane import (
    ControlPlaneContractError,
    RouteDecision,
    RouteExplanation,
    RouteIntent,
    assert_decision_matches_intent,
    assert_explanation_matches_decision,
    canonical_digest,
)
from ..control_plane import ControlPlaneAPI
from ..control_plane.routing.resolver import explain_route_decision
from ..control_plane.routing.snapshot import RoutingSnapshotError
from ..workspace.discovery import Workspace


route_app = typer.Typer(
    help="Resolve, explain, and validate receipt-bound Agent OS route decisions"
)


def _api(
    root: str,
    routing_bundle: str | None,
    source_lock: str | None,
) -> ControlPlaneAPI:
    return ControlPlaneAPI(
        Workspace.discover(root),
        routing_bundle_root=routing_bundle,
        routing_source_lock=source_lock,
    )


def _load(path: str) -> dict[str, Any]:
    payload = json.loads(
        Path(path).expanduser().resolve(strict=False).read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise ValueError("route document must be a JSON object")
    return payload


def _emit(value: Any) -> None:
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True))


def _fail(exc: Exception) -> None:
    typer.echo(f"error: {exc}", err=True)
    raise typer.Exit(code=1) from exc


@route_app.command("resolve")
def route_resolve(
    intent: str = typer.Argument(..., help="RouteIntent JSON path."),
    root: str = typer.Option(".", "--root"),
    routing_bundle: str | None = typer.Option(None, "--routing-bundle"),
    source_lock: str | None = typer.Option(None, "--source-lock"),
) -> None:
    try:
        typed_intent = RouteIntent.model_validate(_load(intent))
        decision = _api(root, routing_bundle, source_lock).resolve(typed_intent)
        assert_decision_matches_intent(typed_intent, decision)
    except (
        OSError,
        json.JSONDecodeError,
        ValidationError,
        ValueError,
        RoutingSnapshotError,
        ControlPlaneContractError,
    ) as exc:
        _fail(exc)
    _emit(decision)


@route_app.command("explain")
def route_explain(
    decision: str = typer.Argument(..., help="RouteDecision JSON path."),
) -> None:
    try:
        typed_decision = RouteDecision.model_validate(_load(decision))
        explanation = explain_route_decision(typed_decision)
        assert_explanation_matches_decision(typed_decision, explanation)
    except (
        OSError,
        json.JSONDecodeError,
        ValidationError,
        ValueError,
        ControlPlaneContractError,
    ) as exc:
        _fail(exc)
    _emit(explanation)


@route_app.command("validate")
def route_validate(
    document: str = typer.Argument(
        ...,
        help="RouteIntent, RouteDecision, or RouteExplanation JSON path.",
    ),
    against: str | None = typer.Option(
        None,
        "--against",
        help="Exact parent RouteIntent or RouteDecision for chain validation.",
    ),
) -> None:
    try:
        payload = _load(document)
        if "intent_id" in payload:
            typed_intent = RouteIntent.model_validate(payload)
            kind = "RouteIntent"
            schema_version = typed_intent.schema_version
            digest = canonical_digest(typed_intent)
        elif "decision_id" in payload and "intent_ref" in payload:
            typed_decision = RouteDecision.model_validate(payload)
            kind = "RouteDecision"
            if against is not None:
                assert_decision_matches_intent(
                    RouteIntent.model_validate(_load(against)),
                    typed_decision,
                )
            schema_version = typed_decision.schema_version
            digest = canonical_digest(typed_decision)
        elif "explanation_id" in payload:
            typed_explanation = RouteExplanation.model_validate(payload)
            kind = "RouteExplanation"
            if against is not None:
                assert_explanation_matches_decision(
                    RouteDecision.model_validate(_load(against)),
                    typed_explanation,
                )
            schema_version = typed_explanation.schema_version
            digest = canonical_digest(typed_explanation)
        else:
            raise ValueError("unrecognized route document shape")
    except (
        OSError,
        json.JSONDecodeError,
        ValidationError,
        ValueError,
        ControlPlaneContractError,
    ) as exc:
        _fail(exc)
    _emit(
        {
            "valid": True,
            "kind": kind,
            "schema_version": schema_version,
            "digest": digest,
            "execution_authorized": False,
        }
    )
