from __future__ import annotations

import json

import typer

from ..api import AoASDK
from ..errors import InvalidSurface


skills_app = typer.Typer(
    help="Inspect owner-scoped skill installations and exact typed capability nodes"
)


@skills_app.command("inspect")
def skills_inspect(
    repo_root: str = typer.Argument(
        ...,
        help="Repository whose owner projection should be inspected.",
    ),
    user_skill_root: str | None = typer.Option(
        None,
        "--user-skill-root",
        help="Override CODEX_HOME/skills or ~/.codex/skills for this inspection.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for owner discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        report = AoASDK.from_workspace(root).skills.inspect(
            repo_root=repo_root,
            user_skill_root=user_skill_root,
        )
    except InvalidSurface as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=True))
        return

    typer.echo(f"repo_root: {report.repo_root}")
    typer.echo(f"source_repo_root: {report.source_repo_root}")
    typer.echo(f"user_skill_root: {report.user_skill_root}")
    typer.echo("roots:")
    for root_report in report.roots:
        typer.echo(
            f"  - {root_report.root_kind}: {root_report.path} "
            f"[{root_report.authority}; {len(root_report.entries)} entries]"
        )
        for entry in root_report.entries:
            typer.echo(f"      {entry.name}: {entry.status}")
    if report.duplicate_names:
        typer.echo("duplicate_names:")
        for name, locations in report.duplicate_names.items():
            typer.echo(f"  - {name}: {', '.join(locations)}")
    if report.warnings:
        typer.echo("warnings:")
        for warning in report.warnings:
            typer.echo(f"  - {warning}")


@skills_app.command("capability")
def skills_capability(
    node_id: str = typer.Argument(..., help="Exact node ID from the aoa-skills capability graph."),
    root: str = typer.Option(".", "--root", help="Workspace root used for owner discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        neighborhood = AoASDK.from_workspace(root).skills.capability(node_id)
    except InvalidSurface as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(
            json.dumps(neighborhood.model_dump(mode="json"), indent=2, ensure_ascii=True)
        )
        return

    node = neighborhood.node
    typer.echo(f"id: {node.id}")
    typer.echo(f"kind: {node.kind}")
    typer.echo(f"contract_level: {node.contract_level}")
    typer.echo(f"owner: {node.owner.repo}:{node.owner.surface}")
    typer.echo(f"lifecycle: {node.lifecycle.state} [{node.lifecycle.visibility}]")
    typer.echo(f"incoming_relations: {len(neighborhood.incoming)}")
    for relation in neighborhood.incoming:
        typer.echo(f"  - {relation.source} -[{relation.kind}]-> {relation.target}")
    typer.echo(f"outgoing_relations: {len(neighborhood.outgoing)}")
    for relation in neighborhood.outgoing:
        typer.echo(f"  - {relation.source} -[{relation.kind}]-> {relation.target}")
