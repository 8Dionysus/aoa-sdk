from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from ..api import AoASDK
from ..closeout import CloseoutAPI
from ..compatibility import CompatibilityAPI
from ..loaders import load_json
from ..models import (
    CheckpointCloseoutContext,
    CheckpointCloseoutExecutionReport,
    CheckpointCaptureResult,
    KernelNextStepBrief,
    OwnerFollowThroughBrief,
    SessionCheckpointNote,
    SessionCheckpointPromotion,
    SurfaceCloseoutHandoff,
    SurfaceDetectionReport,
    SurfaceOpportunityItem,
    SkillDetectionReport,
    SkillDispatchItem,
)
from ..workspace.bootstrap import bootstrap_workspace
from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS

app = typer.Typer(help="AoA SDK CLI")
workspace_app = typer.Typer(help="Inspect workspace topology")
compatibility_app = typer.Typer(help="Inspect compatibility of consumed surfaces")
closeout_app = typer.Typer(help="Run bounded reviewed-session closeout orchestration")
skills_app = typer.Typer(help="Read project skill layers and run phase-aware skill detection/dispatch")
surfaces_app = typer.Typer(help="Read additive AoA surface-detection reports and reviewed closeout handoffs")
checkpoint_app = typer.Typer(help="Capture checkpoint-aware session-growth notes and reviewed promotions")

app.add_typer(workspace_app, name="workspace")
app.add_typer(compatibility_app, name="compatibility")
app.add_typer(closeout_app, name="closeout")
app.add_typer(skills_app, name="skills")
app.add_typer(surfaces_app, name="surfaces")
app.add_typer(checkpoint_app, name="checkpoint")


def _workspace_payload(workspace: Workspace) -> dict[str, Any]:
    repos: dict[str, dict[str, str | None]] = {}
    for repo in KNOWN_REPOS:
        path = workspace.repo_roots.get(repo)
        origin = workspace.repo_origins.get(repo)
        repos[repo] = {
            "path": str(path) if path is not None else None,
            "origin": origin,
        }
    return {
        "root": str(workspace.root),
        "federation_root": str(workspace.federation_root),
        "federation_root_source": workspace.federation_root_source,
        "manifest": str(workspace.manifest_path) if workspace.manifest_path else None,
        "repos": repos,
    }


def _print_kernel_next_brief(brief: KernelNextStepBrief | None, *, indent: str = "") -> None:
    if brief is None:
        return
    typer.echo(f"{indent}kernel_next:")
    typer.echo(f"{indent}  action: {brief.suggested_action}")
    if brief.suggested_skill_name is not None:
        typer.echo(f"{indent}  skill: {brief.suggested_skill_name}")
    if brief.suggested_owner_repo is not None:
        typer.echo(f"{indent}  owner_repo: {brief.suggested_owner_repo}")
    if brief.missing_kernel_skill_names:
        typer.echo(f"{indent}  missing: {', '.join(brief.missing_kernel_skill_names)}")
    typer.echo(f"{indent}  reason: {brief.reason}")


def _print_owner_follow_through(
    briefs: list[OwnerFollowThroughBrief],
    *,
    handoff_path: str | None = None,
    indent: str = "",
) -> None:
    if not briefs:
        return
    typer.echo(f"{indent}owner_follow_through:")
    if handoff_path is not None:
        typer.echo(f"{indent}  handoff: {handoff_path}")
    for item in briefs:
        unit_label = item.unit_name or item.unit_ref
        typer.echo(
            f"{indent}  - [{item.suggested_action}] {unit_label} -> {item.owner_repo}:{item.next_surface}"
        )
        typer.echo(f"{indent}    reason: {item.reason}")


def _print_skill_items(label: str, items: list[SkillDispatchItem]) -> None:
    typer.echo(f"{label}:")
    if not items:
        typer.echo("  - none")
        return
    for item in items:
        family = item.collision_family or "none"
        availability = item.host_availability.status
        typer.echo(f"  - {item.skill_name} [{item.layer} / {family} / {availability}]")
        typer.echo(f"    reason: {item.reason}")
        host_line = f"{item.host_availability.status} via {item.host_availability.source}"
        if item.host_availability.manual_fallback_allowed:
            host_line += "; manual fallback allowed"
        typer.echo(f"    host: {host_line}")


def _print_surface_items(label: str, items: list[SurfaceOpportunityItem]) -> None:
    typer.echo(f"{label}:")
    if not items:
        typer.echo("  - none")
        return
    for item in items:
        typer.echo(
            f"  - {item.display_name} [{item.object_kind} / {item.owner_repo} / {item.state} / {item.execution.lane}]"
        )
        typer.echo(f"    ref: {item.surface_ref}")
        typer.echo(f"    reason: {item.reason}")
        if item.owner_layer_ambiguity_note:
            typer.echo(f"    ambiguity: {item.owner_layer_ambiguity_note}")
        if item.shortlist_hints:
            typer.echo(
                "    shortlist: "
                + ", ".join(
                    f"{hint.owner_repo} ({hint.confidence}/{hint.ambiguity})"
                    for hint in item.shortlist_hints
                )
            )


def _print_skill_detection_report(report: SkillDetectionReport) -> None:
    typer.echo(f"phase: {report.phase}")
    typer.echo(f"repo_root: {report.repo_root}")
    typer.echo(f"foundation_id: {report.foundation_id}")
    _print_skill_items("activate_now", report.activate_now)
    _print_skill_items("must_confirm", report.must_confirm)
    _print_skill_items("suggest_next", report.suggest_next)
    typer.echo(f"host_inventory_provided: {'yes' if report.host_inventory_provided else 'no'}")
    typer.echo(f"actionability_gaps: {', '.join(report.actionability_gaps) if report.actionability_gaps else 'none'}")
    typer.echo(f"blocked_actions: {', '.join(report.blocked_actions) if report.blocked_actions else 'none'}")
    _print_kernel_next_brief(report.closeout_chain)
    typer.echo("reasoning:")
    for line in report.reasoning:
        typer.echo(f"  - {line}")


def _print_surface_detection_report(report: SurfaceDetectionReport) -> None:
    typer.echo(f"phase: {report.phase}")
    typer.echo(f"repo_root: {report.repo_root}")
    typer.echo(f"workspace_root: {report.workspace_root}")
    typer.echo(f"skill_report_path: {report.skill_report_path or 'none'}")
    typer.echo(f"skill_report_included: {'yes' if report.skill_report_included else 'no'}")
    typer.echo(f"shortlist_included: {'yes' if report.shortlist_included else 'no'}")
    typer.echo(f"active_skill_names: {', '.join(report.active_skill_names) if report.active_skill_names else 'none'}")
    typer.echo(
        "immediate_skill_dispatch: "
        f"{', '.join(report.immediate_skill_dispatch) if report.immediate_skill_dispatch else 'none'}"
    )
    if report.phase == "checkpoint":
        typer.echo(f"checkpoint_kind: {report.checkpoint_kind or 'none'}")
        typer.echo(f"checkpoint_should_capture: {'yes' if report.checkpoint_should_capture else 'no'}")
        typer.echo(f"promotion_recommendation: {report.promotion_recommendation}")
        typer.echo(f"blocked_by: {', '.join(report.blocked_by) if report.blocked_by else 'none'}")
        typer.echo("candidate_clusters:")
        if not report.candidate_clusters:
            typer.echo("  - none")
        else:
            for cluster in report.candidate_clusters:
                typer.echo(
                    f"  - {cluster.display_name} [{cluster.candidate_kind} / {cluster.owner_hint} / {cluster.confidence}]"
                )
                typer.echo(f"    candidate_id: {cluster.candidate_id}")
                if cluster.blocked_by:
                    typer.echo(f"    blocked_by: {', '.join(cluster.blocked_by)}")
    _print_surface_items("items", report.items)
    typer.echo(f"closeout_followups: {', '.join(report.closeout_followups) if report.closeout_followups else 'none'}")
    typer.echo(f"owner_layer_notes: {', '.join(report.owner_layer_notes) if report.owner_layer_notes else 'none'}")
    typer.echo(f"actionability_gaps: {', '.join(report.actionability_gaps) if report.actionability_gaps else 'none'}")


def _print_surface_handoff(report: SurfaceCloseoutHandoff) -> None:
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"reviewed: {'yes' if report.reviewed else 'no'}")
    typer.echo(f"surface_detection_report_ref: {report.surface_detection_report_ref}")
    typer.echo(f"checkpoint_note_ref: {report.checkpoint_note_ref or 'none'}")
    typer.echo(f"stats_refresh_recommended: {'yes' if report.stats_refresh_recommended else 'no'}")
    _print_surface_items("surviving_items", report.surviving_items)
    typer.echo("surviving_checkpoint_clusters:")
    if not report.surviving_checkpoint_clusters:
        typer.echo("  - none")
    else:
        for cluster in report.surviving_checkpoint_clusters:
            typer.echo(
                f"  - {cluster.display_name} [{cluster.candidate_kind} / {cluster.owner_hint} / {cluster.review_status}]"
            )
            typer.echo(
                "    session_end_targets: "
                f"{', '.join(cluster.session_end_targets) if cluster.session_end_targets else 'none'}"
            )
    typer.echo("checkpoint_harvest_candidates:")
    if not report.checkpoint_harvest_candidates:
        typer.echo("  - none")
    else:
        for cluster in report.checkpoint_harvest_candidates:
            typer.echo(f"  - {cluster.display_name} [{cluster.candidate_id}]")
    typer.echo("checkpoint_progression_candidates:")
    if not report.checkpoint_progression_candidates:
        typer.echo("  - none")
    else:
        for cluster in report.checkpoint_progression_candidates:
            typer.echo(f"  - {cluster.display_name} [{cluster.candidate_id}]")
    typer.echo("checkpoint_progression_axes:")
    if not report.checkpoint_progression_axes:
        typer.echo("  - none")
    else:
        for signal in report.checkpoint_progression_axes:
            typer.echo(f"  - {signal.axis} -> {signal.movement}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(signal.candidate_ids) if signal.candidate_ids else 'none'}"
            )
    typer.echo("checkpoint_upgrade_candidates:")
    if not report.checkpoint_upgrade_candidates:
        typer.echo("  - none")
    else:
        for cluster in report.checkpoint_upgrade_candidates:
            typer.echo(f"  - {cluster.display_name} [{cluster.candidate_id}]")
    typer.echo("handoff_targets:")
    if not report.handoff_targets:
        typer.echo("  - none")
    else:
        for item in report.handoff_targets:
            typer.echo(f"  - {item.skill_name}")
            typer.echo(f"    why: {item.why}")
            typer.echo(f"    triggered_by: {', '.join(item.triggered_by) if item.triggered_by else 'none'}")
    typer.echo(f"notes: {', '.join(report.notes) if report.notes else 'none'}")


def _print_checkpoint_note(note: SessionCheckpointNote) -> None:
    typer.echo(f"session_ref: {note.session_ref}")
    typer.echo(f"state: {note.state}")
    typer.echo(f"review_status: {note.review_status}")
    typer.echo(f"promotion_recommendation: {note.promotion_recommendation}")
    typer.echo(f"carry_until_session_closeout: {'yes' if note.carry_until_session_closeout else 'no'}")
    typer.echo(f"session_end_recommendation: {note.session_end_recommendation}")
    typer.echo(
        "harvest_candidate_ids: "
        f"{', '.join(note.harvest_candidate_ids) if note.harvest_candidate_ids else 'none'}"
    )
    typer.echo(
        "progression_candidate_ids: "
        f"{', '.join(note.progression_candidate_ids) if note.progression_candidate_ids else 'none'}"
    )
    typer.echo(
        "upgrade_candidate_ids: "
        f"{', '.join(note.upgrade_candidate_ids) if note.upgrade_candidate_ids else 'none'}"
    )
    typer.echo("progression_axis_signals:")
    if not note.progression_axis_signals:
        typer.echo("  - none")
    else:
        for signal in note.progression_axis_signals:
            typer.echo(f"  - {signal.axis} -> {signal.movement}")
            typer.echo(f"    why: {signal.why}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(signal.candidate_ids) if signal.candidate_ids else 'none'}"
            )
    typer.echo(f"stats_refresh_recommended: {'yes' if note.stats_refresh_recommended else 'no'}")
    typer.echo(f"repo_scope: {', '.join(note.repo_scope) if note.repo_scope else 'none'}")
    typer.echo(f"blocked_by: {', '.join(note.blocked_by) if note.blocked_by else 'none'}")
    typer.echo("candidate_clusters:")
    if not note.candidate_clusters:
        typer.echo("  - none")
        return
    for cluster in note.candidate_clusters:
        typer.echo(
            f"  - {cluster.display_name} [{cluster.candidate_kind} / {cluster.owner_hint} / hits={cluster.checkpoint_hits} / {cluster.review_status}]"
        )
        typer.echo(f"    candidate_id: {cluster.candidate_id}")
        typer.echo(
            "    session_end_targets: "
            f"{', '.join(cluster.session_end_targets) if cluster.session_end_targets else 'none'}"
        )
        if cluster.blocked_by:
            typer.echo(f"    blocked_by: {', '.join(cluster.blocked_by)}")


def _print_checkpoint_capture(result: CheckpointCaptureResult | None) -> None:
    if result is None:
        return
    if result.appended:
        typer.echo(
            f"checkpoint_capture: appended ({result.mode}, kind={result.checkpoint_kind}, reason={result.reason})"
        )
    elif not result.attempted:
        typer.echo("checkpoint_capture: disabled")
    else:
        typer.echo(
            f"checkpoint_capture: skipped ({result.mode}, kind={result.checkpoint_kind or 'none'}, reason={result.reason})"
        )
    if result.note_ref:
        typer.echo(f"checkpoint_note_ref: {result.note_ref}")
    if result.progression_axis_signals:
        typer.echo("progression_axis_signals:")
        for signal in result.progression_axis_signals:
            typer.echo(f"  - {signal.axis} -> {signal.movement}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(signal.candidate_ids) if signal.candidate_ids else 'none'}"
            )
    if result.session_end_skill_targets:
        typer.echo("session_end_skill_targets:")
        for target in result.session_end_skill_targets:
            typer.echo(f"  - {target.skill_name} [{target.phase}]")
            typer.echo(f"    why: {target.why}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(target.candidate_ids) if target.candidate_ids else 'none'}"
            )
    else:
        typer.echo("session_end_skill_targets: none")
    typer.echo(f"stats_refresh_recommended: {'yes' if result.stats_refresh_recommended else 'no'}")
    if result.session_end_next_honest_move:
        typer.echo(f"session_end_next_honest_move: {result.session_end_next_honest_move}")


def _print_checkpoint_promotion(promotion: SessionCheckpointPromotion) -> None:
    typer.echo(f"session_ref: {promotion.session_ref}")
    typer.echo(f"target: {promotion.target}")
    typer.echo(f"resulting_state: {promotion.resulting_state}")
    typer.echo(f"source_note_ref: {promotion.source_note_ref}")
    typer.echo(f"output_refs: {', '.join(promotion.output_refs) if promotion.output_refs else 'none'}")


def _print_closeout_context(context: CheckpointCloseoutContext) -> None:
    typer.echo(f"session_ref: {context.session_ref}")
    typer.echo(f"orchestrator_skill_name: {context.orchestrator_skill_name}")
    typer.echo(f"repo_root: {context.repo_root}")
    typer.echo(f"reviewed_artifact_ref: {context.reviewed_artifact_ref}")
    typer.echo(f"checkpoint_note_ref: {context.checkpoint_note_ref or 'none'}")
    typer.echo(f"surface_handoff_ref: {context.surface_handoff_ref or 'none'}")
    typer.echo(f"receipt_refs: {', '.join(context.receipt_refs) if context.receipt_refs else 'none'}")
    typer.echo(f"repo_scope: {', '.join(context.repo_scope) if context.repo_scope else 'none'}")
    typer.echo(
        "candidate_map: "
        f"harvest={len(context.candidate_map.harvest_candidate_ids)}, "
        f"progression={len(context.candidate_map.progression_candidate_ids)}, "
        f"upgrade={len(context.candidate_map.upgrade_candidate_ids)}"
    )
    typer.echo("ordered_skill_plan:")
    if not context.ordered_skill_plan:
        typer.echo("  - none")
    else:
        for target in context.ordered_skill_plan:
            typer.echo(f"  - {target.skill_name}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(target.candidate_ids) if target.candidate_ids else 'none'}"
            )
            typer.echo(f"    why: {target.why}")
    typer.echo(f"notes: {', '.join(context.notes) if context.notes else 'none'}")


def _print_closeout_execution_report(report: CheckpointCloseoutExecutionReport) -> None:
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"orchestrator_skill_name: {report.orchestrator_skill_name}")
    typer.echo(f"context_ref: {report.context_ref}")
    typer.echo(f"reviewed_artifact_ref: {report.reviewed_artifact_ref}")
    typer.echo(f"checkpoint_note_ref: {report.checkpoint_note_ref or 'none'}")
    typer.echo(f"surface_handoff_ref: {report.surface_handoff_ref or 'none'}")
    typer.echo("executed_skills:")
    if not report.executed_skills:
        typer.echo("  - none")
    else:
        for item in report.executed_skills:
            typer.echo(f"  - {item.skill_name}")
            typer.echo(f"    reason: {item.reason}")
            typer.echo(
                "    artifact_refs: "
                f"{', '.join(item.artifact_refs) if item.artifact_refs else 'none'}"
            )
            typer.echo(
                "    receipt_refs: "
                f"{', '.join(item.receipt_refs) if item.receipt_refs else 'none'}"
            )
    typer.echo("skipped_skills:")
    if not report.skipped_skills:
        typer.echo("  - none")
    else:
        for item in report.skipped_skills:
            typer.echo(f"  - {item.skill_name}: {item.reason}")
    typer.echo(
        "produced_artifact_refs: "
        f"{', '.join(report.produced_artifact_refs) if report.produced_artifact_refs else 'none'}"
    )
    typer.echo(
        "produced_receipt_refs: "
        f"{', '.join(report.produced_receipt_refs) if report.produced_receipt_refs else 'none'}"
    )
    typer.echo(f"final_stop_reason: {report.final_stop_reason}")


def _resolve_host_available_skills(
    *,
    host_skills: list[str],
    host_skill_manifest: str | None,
) -> tuple[list[str] | None, str]:
    if host_skills:
        return list(dict.fromkeys(skill_name for skill_name in host_skills if skill_name)), "host-skill-list"
    if host_skill_manifest is None:
        return None, "not-provided"

    manifest_path = Path(host_skill_manifest).expanduser().resolve()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise typer.BadParameter(f"could not read host skill manifest: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"host skill manifest is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise typer.BadParameter("host skill manifest must be a JSON object with a non-empty string list at 'skills'")
    skills = payload.get("skills")
    if not isinstance(skills, list) or not all(isinstance(item, str) and item for item in skills):
        raise typer.BadParameter("host skill manifest must be a JSON object with a non-empty string list at 'skills'")
    return list(dict.fromkeys(skills)), "host-manifest"


def _resolve_context_root(workspace: Workspace, repo_root: str) -> Path:
    resolved_repo_root = Path(repo_root).expanduser()
    if not resolved_repo_root.is_absolute():
        return (workspace.root / resolved_repo_root).resolve()
    return resolved_repo_root.resolve()


def _resolve_context_label(workspace: Workspace, repo_root: str) -> str:
    resolved_repo_root = _resolve_context_root(workspace, repo_root)
    return "workspace" if resolved_repo_root == workspace.federation_root else resolved_repo_root.name


def _resolve_skill_report_path(
    *,
    workspace: Workspace,
    repo_root: str,
    phase: str,
    mutation_surface: str = "none",
    report_output: str | None = None,
) -> Path:
    if report_output is not None:
        return Path(report_output).expanduser().resolve()

    label = _resolve_context_label(workspace, repo_root)
    suffix = phase
    if phase == "pre-mutation":
        suffix = f"{phase}-{mutation_surface}"
    return workspace.repo_path("aoa-sdk") / ".aoa" / "skill-dispatch" / f"{label}.{suffix}.latest.json"


def _write_skill_report(path: Path, report: SkillDetectionReport) -> dict[str, Any]:
    payload = {
        "report_path": str(path),
        "report": report.model_dump(mode="json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload


def _resolve_surface_report_path(
    *,
    workspace: Workspace,
    repo_root: str,
    phase: str,
    report_output: str | None = None,
) -> Path:
    if report_output is not None:
        return Path(report_output).expanduser().resolve()
    label = _resolve_context_label(workspace, repo_root)
    return workspace.repo_path("aoa-sdk") / ".aoa" / "surface-detection" / f"{label}.{phase}.latest.json"


def _resolve_surface_handoff_path(
    *,
    workspace: Workspace,
    repo_root: str,
    report_output: str | None = None,
) -> Path:
    if report_output is not None:
        return Path(report_output).expanduser().resolve()
    label = _resolve_context_label(workspace, repo_root)
    return workspace.repo_path("aoa-sdk") / ".aoa" / "surface-detection" / f"{label}.closeout-handoff.latest.json"


def _write_surface_report(path: Path, report: SurfaceDetectionReport) -> dict[str, Any]:
    payload = {
        "report_path": str(path),
        "report": report.model_dump(mode="json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload


def _merge_checkpoint_note(payload: dict[str, Any], note: SessionCheckpointNote | None) -> dict[str, Any]:
    if note is None:
        return payload
    merged = dict(payload)
    merged["checkpoint_note"] = note.model_dump(mode="json")
    return merged


def _merge_checkpoint_capture(payload: dict[str, Any], result: CheckpointCaptureResult | None) -> dict[str, Any]:
    if result is None:
        return payload
    merged = dict(payload)
    merged["checkpoint_capture"] = result.model_dump(mode="json", exclude={"note"})
    if result.note is not None:
        merged["checkpoint_note"] = result.note.model_dump(mode="json")
    return merged


def _write_surface_handoff(path: Path, report: SurfaceCloseoutHandoff) -> dict[str, Any]:
    payload = {
        "report_path": str(path),
        "report": report.model_dump(mode="json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload


def _load_surface_detection_report(path: str) -> SurfaceDetectionReport:
    payload = load_json(Path(path).expanduser().resolve())
    report_payload = payload.get("report", payload)
    return SurfaceDetectionReport.model_validate(report_payload)


@app.command()
def version() -> None:
    print("aoa-sdk 0.1.0")


@workspace_app.command("inspect")
def workspace_inspect(
    root: str = typer.Argument("."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    payload = _workspace_payload(workspace)

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"root: {payload['root']}")
    typer.echo(f"federation_root: {payload['federation_root']}")
    typer.echo(f"federation_root_source: {payload['federation_root_source']}")
    typer.echo(f"manifest: {payload['manifest'] or 'none'}")

    for repo in KNOWN_REPOS:
        repo_payload = payload["repos"][repo]
        path = repo_payload["path"]
        origin = repo_payload["origin"]
        if path is None:
            typer.echo(f"{repo}: missing")
            continue
        typer.echo(f"{repo}: {path} [{origin}]")


@workspace_app.command("bootstrap")
def workspace_bootstrap(
    target_root: str = typer.Argument(..., help="Sibling-workspace root that already contains the public repos."),
    mode: str = typer.Option("symlink", "--mode", help="Foundation install mode: symlink or copy."),
    execute: bool = typer.Option(False, "--execute", help="Apply the bootstrap plan instead of only reporting it."),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Replace conflicting foundation installs when the current target does not match the source export.",
    ),
    write_agents: bool = typer.Option(
        True,
        "--write-agents/--no-write-agents",
        help="Write one root-level AGENTS.md when it is missing.",
    ),
    overwrite_agents: bool = typer.Option(
        False,
        "--overwrite-agents",
        help="Replace an existing root-level AGENTS.md with the canonical workspace guidance.",
    ),
    allow_partial: bool = typer.Option(
        False,
        "--allow-partial",
        help="Allow bootstrap planning even when the canonical sibling workspace is incomplete.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = bootstrap_workspace(
        target_root,
        mode=mode,  # type: ignore[arg-type]
        execute=execute,
        overwrite=overwrite,
        write_agents=write_agents,
        overwrite_agents=overwrite_agents,
        strict_layout=not allow_partial,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        typer.echo(f"workspace_root: {report.workspace_root}")
        typer.echo(f"foundation_id: {report.foundation_id}")
        typer.echo(f"profile: {report.canonical_install_profile}")
        typer.echo(f"ready: {report.ready}")
        typer.echo(f"executed: {report.executed}")
        typer.echo(f"verified: {report.verified if report.verified is not None else 'not-run'}")
        typer.echo(f"missing_required_repos: {', '.join(report.missing_required_repos) or 'none'}")
        if report.agents_file is not None:
            typer.echo(f"root_agents: {report.agents_file.path} [{report.agents_file.action}]")
        typer.echo("install_steps:")
        for step in report.install_steps:
            typer.echo(f"  - {step.skill_name}: {step.action}")
        if report.warnings:
            typer.echo("warnings:")
            for warning in report.warnings:
                typer.echo(f"  - {warning}")
        if report.blockers:
            typer.echo("blockers:")
            for blocker in report.blockers:
                typer.echo(f"  - {blocker}")
    if not report.ready or (execute and report.verified is not True):
        raise typer.Exit(code=1)


@compatibility_app.command("check")
def compatibility_check(
    root: str = typer.Argument("."),
    repo: str | None = typer.Option(None, "--repo", help="Restrict checks to one repo."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    compatibility = CompatibilityAPI(workspace)

    if repo is not None and repo not in KNOWN_REPOS:
        raise typer.BadParameter(f"unknown repo {repo!r}")

    checks = compatibility.check_repo(repo) if repo is not None else compatibility.check_all()
    if repo is not None and not checks:
        raise typer.BadParameter(f"no compatibility rules registered for repo {repo!r}")

    payload = {
        "root": str(workspace.root),
        "federation_root": str(workspace.federation_root),
        "repo": repo,
        "compatible": all(check.compatible for check in checks),
        "checks": [check.model_dump(mode="json") for check in checks],
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        typer.echo(f"root: {payload['root']}")
        typer.echo(f"federation_root: {payload['federation_root']}")
        typer.echo(f"repo: {repo or 'all'}")
        for check in checks:
            status = "ok" if check.compatible else "fail"
            typer.echo(f"{status}: {check.surface_id} -> {check.reason}")

    if not payload["compatible"]:
        raise typer.Exit(code=1)


@skills_app.command("detect")
def skills_detect(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as task context."),
    phase: str = typer.Option(..., "--phase", help="Detection phase: ingress, pre-mutation, checkpoint, or closeout."),
    intent_text: str = typer.Option("", "--intent-text", help="Intent text used for tiny-router style matching."),
    mutation_surface: str = typer.Option(
        "none",
        "--mutation-surface",
        help="Mutation class: none, code, repo-config, infra, runtime, or public-share.",
    ),
    closeout_path: str | None = typer.Option(
        None,
        "--closeout-path",
        help="Optional closeout report or manifest path when phase=closeout.",
    ),
    host_skill: list[str] = typer.Option(
        None,
        "--host-skill",
        help="Repeatable host-visible skill name used to annotate recommendation availability.",
    ),
    host_skill_manifest: str | None = typer.Option(
        None,
        "--host-skill-manifest",
        help="Optional JSON manifest with {'skills': [...]} used to annotate host-visible skill availability.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    host_available_skills, host_availability_source = _resolve_host_available_skills(
        host_skills=host_skill,
        host_skill_manifest=host_skill_manifest,
    )
    sdk_report = AoASDK.from_workspace(root).skills.detect(
        repo_root=repo_root,
        phase=phase,  # type: ignore[arg-type]
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        closeout_path=closeout_path,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    payload = sdk_report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_skill_detection_report(sdk_report)


@skills_app.command("dispatch")
def skills_dispatch(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as task context."),
    phase: str = typer.Option(..., "--phase", help="Dispatch phase: ingress, pre-mutation, checkpoint, or closeout."),
    intent_text: str = typer.Option("", "--intent-text", help="Intent text used for tiny-router style matching."),
    mutation_surface: str = typer.Option(
        "none",
        "--mutation-surface",
        help="Mutation class: none, code, repo-config, infra, runtime, or public-share.",
    ),
    closeout_path: str | None = typer.Option(
        None,
        "--closeout-path",
        help="Optional closeout report or manifest path when phase=closeout.",
    ),
    session_file: str | None = typer.Option(
        None,
        "--session-file",
        help="Optional skill runtime session file. Defaults to the canonical session contract path.",
    ),
    host_skill: list[str] = typer.Option(
        None,
        "--host-skill",
        help="Repeatable host-visible skill name used to annotate recommendation availability.",
    ),
    host_skill_manifest: str | None = typer.Option(
        None,
        "--host-skill-manifest",
        help="Optional JSON manifest with {'skills': [...]} used to annotate host-visible skill availability.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    host_available_skills, host_availability_source = _resolve_host_available_skills(
        host_skills=host_skill,
        host_skill_manifest=host_skill_manifest,
    )
    sdk_report = AoASDK.from_workspace(root).skills.dispatch(
        repo_root=repo_root,
        phase=phase,  # type: ignore[arg-type]
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        closeout_path=closeout_path,
        session_file=session_file,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    payload = sdk_report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_skill_detection_report(sdk_report)


@skills_app.command("enter")
def skills_enter(
    repo_root: str = typer.Argument(".", help="Repository root or workspace root used as task context."),
    intent_text: str = typer.Option("", "--intent-text", help="Short task summary used for ingress detection."),
    session_file: str | None = typer.Option(
        None,
        "--session-file",
        help="Optional skill runtime session file. Defaults to the canonical session contract path.",
    ),
    report_output: str | None = typer.Option(
        None,
        "--report-output",
        help="Optional JSON path for the persisted ingress dispatch report.",
    ),
    checkpoint_kind: str | None = typer.Option(
        None,
        "--checkpoint-kind",
        help="Optional explicit checkpoint kind to append after ingress dispatch: manual, commit, verify_green, pr_opened, pr_merged, pause, or owner_followthrough.",
    ),
    mark_checkpoint_reviewable: bool = typer.Option(
        False,
        "--mark-checkpoint-reviewable",
        help="When a checkpoint is appended explicitly or automatically, mark it as manually reviewable.",
    ),
    auto_checkpoint: bool = typer.Option(
        True,
        "--auto-checkpoint/--no-auto-checkpoint",
        help="Auto-append one local checkpoint note only when checkpoint-phase surface detection finds a real growth signal.",
    ),
    host_skill: list[str] = typer.Option(
        None,
        "--host-skill",
        help="Repeatable host-visible skill name used to annotate recommendation availability.",
    ),
    host_skill_manifest: str | None = typer.Option(
        None,
        "--host-skill-manifest",
        help="Optional JSON manifest with {'skills': [...]} used to annotate host-visible skill availability.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    sdk = AoASDK.from_workspace(root)
    host_available_skills, host_availability_source = _resolve_host_available_skills(
        host_skills=host_skill,
        host_skill_manifest=host_skill_manifest,
    )
    sdk_report = sdk.skills.dispatch(
        repo_root=repo_root,
        phase="ingress",
        intent_text=intent_text,
        mutation_surface="none",
        session_file=session_file,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    report_path = _resolve_skill_report_path(
        workspace=workspace,
        repo_root=repo_root,
        phase="ingress",
        report_output=report_output,
    )
    payload = _write_skill_report(report_path, sdk_report)
    checkpoint_capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=repo_root,
        phase="ingress",
        intent_text=intent_text,
        mutation_surface="none",
        session_file=session_file,
        skill_report_path=str(report_path),
        checkpoint_kind=checkpoint_kind,  # type: ignore[arg-type]
        manual_review_requested=mark_checkpoint_reviewable,
        auto_capture=auto_checkpoint,
    )
    payload = _merge_checkpoint_capture(payload, checkpoint_capture)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {payload['report_path']}")
    _print_checkpoint_capture(checkpoint_capture)
    if checkpoint_capture.note is not None:
        typer.echo(f"checkpoint_note_state: {checkpoint_capture.note.state}")
        typer.echo(f"checkpoint_recommendation: {checkpoint_capture.note.promotion_recommendation}")
    _print_skill_detection_report(sdk_report)


@skills_app.command("guard")
def skills_guard(
    repo_root: str = typer.Argument(..., help="Repository root or workspace root used as task context."),
    intent_text: str = typer.Option("", "--intent-text", help="Short task summary used for pre-mutation detection."),
    mutation_surface: str = typer.Option(
        "code",
        "--mutation-surface",
        help="Mutation class: code, repo-config, infra, runtime, or public-share.",
    ),
    session_file: str | None = typer.Option(
        None,
        "--session-file",
        help="Optional skill runtime session file. Defaults to the canonical session contract path.",
    ),
    report_output: str | None = typer.Option(
        None,
        "--report-output",
        help="Optional JSON path for the persisted pre-mutation dispatch report.",
    ),
    checkpoint_kind: str | None = typer.Option(
        None,
        "--checkpoint-kind",
        help="Optional explicit checkpoint kind to append after guard dispatch: manual, commit, verify_green, pr_opened, pr_merged, pause, or owner_followthrough.",
    ),
    mark_checkpoint_reviewable: bool = typer.Option(
        False,
        "--mark-checkpoint-reviewable",
        help="When a checkpoint is appended explicitly or automatically, mark it as manually reviewable.",
    ),
    auto_checkpoint: bool = typer.Option(
        True,
        "--auto-checkpoint/--no-auto-checkpoint",
        help="Auto-append one local checkpoint note only when checkpoint-phase surface detection finds a real growth signal.",
    ),
    host_skill: list[str] = typer.Option(
        None,
        "--host-skill",
        help="Repeatable host-visible skill name used to annotate recommendation availability.",
    ),
    host_skill_manifest: str | None = typer.Option(
        None,
        "--host-skill-manifest",
        help="Optional JSON manifest with {'skills': [...]} used to annotate host-visible skill availability.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    sdk = AoASDK.from_workspace(root)
    host_available_skills, host_availability_source = _resolve_host_available_skills(
        host_skills=host_skill,
        host_skill_manifest=host_skill_manifest,
    )
    sdk_report = sdk.skills.dispatch(
        repo_root=repo_root,
        phase="pre-mutation",
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        session_file=session_file,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    report_path = _resolve_skill_report_path(
        workspace=workspace,
        repo_root=repo_root,
        phase="pre-mutation",
        mutation_surface=mutation_surface,
        report_output=report_output,
    )
    payload = _write_skill_report(report_path, sdk_report)
    checkpoint_capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=repo_root,
        phase="pre-mutation",
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        session_file=session_file,
        skill_report_path=str(report_path),
        checkpoint_kind=checkpoint_kind,  # type: ignore[arg-type]
        manual_review_requested=mark_checkpoint_reviewable,
        auto_capture=auto_checkpoint,
    )
    payload = _merge_checkpoint_capture(payload, checkpoint_capture)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {payload['report_path']}")
    _print_checkpoint_capture(checkpoint_capture)
    if checkpoint_capture.note is not None:
        typer.echo(f"checkpoint_note_state: {checkpoint_capture.note.state}")
        typer.echo(f"checkpoint_recommendation: {checkpoint_capture.note.promotion_recommendation}")
    _print_skill_detection_report(sdk_report)


@surfaces_app.command("detect")
def surfaces_detect(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as task context."),
    phase: str = typer.Option(..., "--phase", help="Detection phase: ingress, in-flight, pre-mutation, checkpoint, or closeout."),
    intent_text: str = typer.Option("", "--intent-text", help="Intent text used for additive surface detection."),
    mutation_surface: str = typer.Option(
        "none",
        "--mutation-surface",
        help="Mutation class: none, code, repo-config, infra, runtime, or public-share.",
    ),
    session_file: str | None = typer.Option(
        None,
        "--session-file",
        help="Optional skill runtime session file used to read active skill names.",
    ),
    closeout_path: str | None = typer.Option(
        None,
        "--closeout-path",
        help="Optional closeout report or manifest path when phase=closeout.",
    ),
    skill_report_path: str | None = typer.Option(
        None,
        "--skill-report-path",
        help="Optional reference to an existing persisted skill report used as prelude context.",
    ),
    report_output: str | None = typer.Option(
        None,
        "--report-output",
        help="Optional JSON path for the persisted surface-detection report.",
    ),
    checkpoint_kind: str | None = typer.Option(
        None,
        "--checkpoint-kind",
        help="Optional checkpoint kind when phase=checkpoint: manual, commit, verify_green, pr_opened, pr_merged, pause, or owner_followthrough.",
    ),
    append_note: bool = typer.Option(
        False,
        "--append-note",
        help="When phase=checkpoint, append the detected checkpoint note into aoa-sdk local session-growth storage.",
    ),
    mark_checkpoint_reviewable: bool = typer.Option(
        False,
        "--mark-checkpoint-reviewable",
        help="When used with --append-note, mark the appended checkpoint as manually reviewable.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    sdk = AoASDK.from_workspace(root)
    if append_note and phase != "checkpoint":
        raise typer.BadParameter("--append-note is only valid when --phase checkpoint")
    if append_note and checkpoint_kind is None:
        raise typer.BadParameter("--append-note requires --checkpoint-kind")
    report = sdk.surfaces.detect(
        repo_root=repo_root,
        phase=phase,  # type: ignore[arg-type]
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        session_file=session_file,
        closeout_path=closeout_path,
        skill_report_path=skill_report_path,
        checkpoint_kind=checkpoint_kind,  # type: ignore[arg-type]
    )
    report_path = _resolve_surface_report_path(
        workspace=workspace,
        repo_root=repo_root,
        phase=phase,
        report_output=report_output,
    )
    payload = _write_surface_report(report_path, report)
    checkpoint_note: SessionCheckpointNote | None = None
    if append_note:
        checkpoint_note = sdk.checkpoints.append(
            repo_root=repo_root,
            checkpoint_kind=checkpoint_kind,  # type: ignore[arg-type]
            intent_text=intent_text,
            mutation_surface=mutation_surface,  # type: ignore[arg-type]
            session_file=session_file,
            skill_report_path=skill_report_path,
            surface_report=report,
            surface_report_path=str(report_path),
            manual_review_requested=mark_checkpoint_reviewable,
        )
        payload = _merge_checkpoint_note(payload, checkpoint_note)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {payload['report_path']}")
    if checkpoint_note is not None:
        typer.echo(f"checkpoint_note_state: {checkpoint_note.state}")
        typer.echo(f"checkpoint_recommendation: {checkpoint_note.promotion_recommendation}")
    _print_surface_detection_report(report)


@surfaces_app.command("handoff")
def surfaces_handoff(
    surface_report: str = typer.Argument(..., help="Path to a persisted surface-detection report."),
    session_ref: str = typer.Option(..., "--session-ref", help="Canonical session_ref for the reviewed route."),
    reviewed: bool = typer.Option(
        True,
        "--reviewed/--not-reviewed",
        help="Surface closeout handoff is allowed only for reviewed routes.",
    ),
    report_output: str | None = typer.Option(
        None,
        "--report-output",
        help="Optional JSON path for the persisted surface closeout handoff report.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    if not reviewed:
        raise typer.BadParameter("surface closeout handoff requires reviewed routes; use --reviewed for the real handoff path")

    workspace = Workspace.discover(root)
    surface_detection_report = _load_surface_detection_report(surface_report)
    report = AoASDK.from_workspace(root).surfaces.build_closeout_handoff(
        surface_report,
        session_ref=session_ref,
        reviewed=reviewed,
    )
    payload = _write_surface_handoff(
        _resolve_surface_handoff_path(
            workspace=workspace,
            repo_root=surface_detection_report.repo_root,
            report_output=report_output,
        ),
        report,
    )
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {payload['report_path']}")
    _print_surface_handoff(report)


@checkpoint_app.command("append")
def checkpoint_append(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the checkpoint context."),
    kind: str = typer.Option(
        ...,
        "--kind",
        help="Checkpoint kind: manual, commit, verify_green, pr_opened, pr_merged, pause, or owner_followthrough.",
    ),
    intent_text: str = typer.Option("", "--intent-text", help="Intent text used for checkpoint-aware surface detection."),
    mutation_surface: str = typer.Option(
        "none",
        "--mutation-surface",
        help="Mutation class: none, code, repo-config, infra, runtime, or public-share.",
    ),
    session_file: str | None = typer.Option(
        None,
        "--session-file",
        help="Optional skill runtime session file used to read active skill names.",
    ),
    skill_report_path: str | None = typer.Option(
        None,
        "--skill-report-path",
        help="Optional reference to an existing persisted skill report used as prelude context.",
    ),
    mark_reviewable: bool = typer.Option(
        False,
        "--mark-reviewable",
        help="Mark this checkpoint as manually reviewable even if repeat density is still low.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    note = AoASDK.from_workspace(root).checkpoints.append(
        repo_root=repo_root,
        checkpoint_kind=kind,  # type: ignore[arg-type]
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        session_file=session_file,
        skill_report_path=skill_report_path,
        manual_review_requested=mark_reviewable,
    )
    payload = note.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_note(note)


@checkpoint_app.command("status")
def checkpoint_status(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the checkpoint context."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    note = AoASDK.from_workspace(root).checkpoints.status(repo_root=repo_root)
    payload = note.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_note(note)


@checkpoint_app.command("promote")
def checkpoint_promote(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the checkpoint context."),
    target: str = typer.Option(
        ...,
        "--target",
        help="Promotion target: dionysus-note or harvest-handoff.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    promotion = AoASDK.from_workspace(root).checkpoints.promote(
        repo_root=repo_root,
        target=target,  # type: ignore[arg-type]
    )
    payload = promotion.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_promotion(promotion)


@checkpoint_app.command("build-closeout-context")
def checkpoint_build_closeout_context(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the closeout context."),
    reviewed_artifact: str = typer.Option(
        ...,
        "--reviewed-artifact",
        help="Reviewed session artifact that the explicit closeout chain must reread.",
    ),
    session_ref: str | None = typer.Option(
        None,
        "--session-ref",
        help="Optional explicit session_ref override when it cannot be derived from the reviewed artifact, receipts, or local note.",
    ),
    receipt_path: list[str] = typer.Option(
        None,
        "--receipt-path",
        help="Receipt JSON or JSONL file that should be included in the closeout evidence bundle. Repeat for multiple files.",
    ),
    receipt_dir: list[str] = typer.Option(
        None,
        "--receipt-dir",
        help="Directory whose JSON or JSONL receipts should be included in the closeout evidence bundle. Repeat for multiple directories.",
    ),
    surface_handoff_path: str | None = typer.Option(
        None,
        "--surface-handoff-path",
        help="Optional reviewed surface handoff path. Defaults to the latest local reviewed handoff for the repo label.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    context = AoASDK.from_workspace(root).checkpoints.build_closeout_context(
        repo_root=repo_root,
        reviewed_artifact_path=reviewed_artifact,
        session_ref=session_ref,
        receipt_paths=receipt_path or [],
        receipt_dirs=receipt_dir or [],
        surface_handoff_path=surface_handoff_path,
    )
    payload = context.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_closeout_context(context)


@checkpoint_app.command("execute-closeout-chain")
def checkpoint_execute_closeout_chain(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the closeout context."),
    reviewed_artifact: str = typer.Option(
        ...,
        "--reviewed-artifact",
        help="Reviewed session artifact that the explicit closeout chain must reread.",
    ),
    session_ref: str | None = typer.Option(
        None,
        "--session-ref",
        help="Optional explicit session_ref override when it cannot be derived from the reviewed artifact, receipts, or local note.",
    ),
    receipt_path: list[str] = typer.Option(
        None,
        "--receipt-path",
        help="Receipt JSON or JSONL file that should be included in the closeout evidence bundle. Repeat for multiple files.",
    ),
    receipt_dir: list[str] = typer.Option(
        None,
        "--receipt-dir",
        help="Directory whose JSON or JSONL receipts should be included in the closeout evidence bundle. Repeat for multiple directories.",
    ),
    surface_handoff_path: str | None = typer.Option(
        None,
        "--surface-handoff-path",
        help="Optional reviewed surface handoff path. Defaults to the latest local reviewed handoff for the repo label.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = AoASDK.from_workspace(root).checkpoints.execute_closeout_chain(
        repo_root=repo_root,
        reviewed_artifact_path=reviewed_artifact,
        session_ref=session_ref,
        receipt_paths=receipt_path or [],
        receipt_dirs=receipt_dir or [],
        surface_handoff_path=surface_handoff_path,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_closeout_execution_report(report)


@closeout_app.command("run")
def closeout_run(
    manifest: str = typer.Argument(..., help="Path to the reviewed session closeout manifest."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional JSON path where the closeout report should be written."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.run(manifest, report_output=report_output)
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"closeout_id: {report.closeout_id}")
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"manifest: {report.manifest_path}")
    typer.echo(f"trigger: {report.trigger}")
    typer.echo(f"reviewed: {report.reviewed}")
    typer.echo(f"audit_only: {report.audit_only}")
    for item in report.publisher_runs:
        typer.echo(
            f"published: {item.publisher} -> {item.log_path} "
            f"(appended={item.appended_count if item.appended_count is not None else 'unknown'}, "
            f"skipped={item.duplicate_skip_count if item.duplicate_skip_count is not None else 'unknown'})"
        )
    if not report.stats_refresh.command:
        typer.echo(report.stats_refresh.stdout or "stats: skipped")
    elif report.stats_refresh.cleared:
        typer.echo(
            f"stats: cleared live state across {report.stats_refresh.source_count or 'unknown'} sources"
        )
    else:
        typer.echo(
            f"stats: refreshed {report.stats_refresh.receipt_count or 'unknown'} receipts "
            f"from {report.stats_refresh.source_count or 'unknown'} sources"
        )
    _print_kernel_next_brief(report.kernel_next_step_brief)
    _print_owner_follow_through(
        report.owner_follow_through_briefs,
        handoff_path=report.owner_handoff_path,
    )
    if report_output:
        typer.echo(f"report: {report_output}")


@closeout_app.command("build-manifest")
def closeout_build_manifest(
    request: str = typer.Argument(..., help="Path to the reviewed closeout build request."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    manifest_dir: str | None = typer.Option(
        None, "--manifest-dir", help="Override the canonical built-manifest directory."
    ),
    enqueue: bool = typer.Option(
        False, "--enqueue", help="Immediately enqueue the built manifest into the canonical inbox."
    ),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the canonical inbox directory."),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Replace an existing built or queued manifest with the same closeout id."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.build_manifest(
        request,
        manifest_dir=manifest_dir,
        enqueue=enqueue,
        inbox_dir=inbox_dir,
        overwrite=overwrite,
    )
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"closeout_id: {report.closeout_id}")
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"request: {report.request_path}")
    typer.echo(f"manifest: {report.manifest_path}")
    typer.echo(f"reviewed_artifact: {report.reviewed_artifact_path}")
    typer.echo(f"audit_only: {report.audit_only}")
    if report.enqueue_report is not None:
        typer.echo(f"queued_manifest: {report.enqueue_report.queued_manifest_path}")
        typer.echo(f"queue_depth: {report.enqueue_report.queue_depth}")


@closeout_app.command("submit-reviewed")
def closeout_submit_reviewed(
    reviewed_artifact: str = typer.Argument(..., help="Path to the reviewed session artifact."),
    session_ref: str = typer.Option(..., "--session-ref", help="Canonical session_ref for the reviewed session."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    receipt_paths: list[str] = typer.Option(
        None,
        "--receipt-path",
        help="Receipt JSON or JSONL file to include in the closeout request. Repeat for multiple files.",
    ),
    receipt_dirs: list[str] = typer.Option(
        None,
        "--receipt-dir",
        help="Directory scanned for receipt JSON or JSONL files. Repeat for multiple directories.",
    ),
    closeout_id: str | None = typer.Option(None, "--closeout-id", help="Optional explicit closeout id."),
    audit_refs: list[str] = typer.Option(
        None,
        "--audit-ref",
        help="Extra reviewed audit artifact that should be carried into the closeout request.",
    ),
    trigger: str = typer.Option("reviewed-closeout", "--trigger", help="Closeout trigger label."),
    notes: str | None = typer.Option(None, "--notes", help="Optional closeout notes."),
    request_dir: str | None = typer.Option(None, "--request-dir", help="Override the canonical request directory."),
    manifest_dir: str | None = typer.Option(
        None, "--manifest-dir", help="Override the canonical built-manifest directory."
    ),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the canonical inbox directory."),
    enqueue: bool = typer.Option(
        True, "--enqueue/--no-enqueue", help="Immediately enqueue the built manifest into the canonical inbox."
    ),
    allow_empty: bool = typer.Option(
        False,
        "--allow-empty",
        help="Allow audit-only reviewed closeout submission when the outer wrapper has no owner-local receipt bundle yet.",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Replace an existing request, built manifest, or queued manifest with the same id."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.submit_reviewed(
        reviewed_artifact,
        session_ref=session_ref,
        receipt_paths=receipt_paths or [],
        receipt_dirs=receipt_dirs or [],
        closeout_id=closeout_id,
        audit_refs=audit_refs or [],
        trigger=trigger,
        notes=notes,
        request_dir=request_dir,
        manifest_dir=manifest_dir,
        inbox_dir=inbox_dir,
        enqueue=enqueue,
        overwrite=overwrite,
        allow_empty=allow_empty,
    )
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"closeout_id: {report.closeout_id}")
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"request: {report.request_path}")
    typer.echo(f"reviewed_artifact: {report.reviewed_artifact_path}")
    typer.echo(f"audit_only: {report.audit_only}")
    typer.echo(f"receipt_count: {len(report.receipt_paths)}")
    typer.echo(f"publishers: {', '.join(report.detected_publishers)}")
    typer.echo(f"manifest: {report.build_report.manifest_path}")
    if report.build_report.enqueue_report is not None:
        typer.echo(f"queued_manifest: {report.build_report.enqueue_report.queued_manifest_path}")
        typer.echo(f"queue_depth: {report.build_report.enqueue_report.queue_depth}")


@closeout_app.command("enqueue-current")
def closeout_enqueue_current(
    manifest: str = typer.Argument(..., help="Path to the reviewed closeout manifest to queue."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the canonical inbox directory."),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Replace an existing queued manifest with the same closeout id."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.enqueue(manifest, inbox_dir=inbox_dir, overwrite=overwrite)
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"closeout_id: {report.closeout_id}")
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"source_manifest: {report.source_manifest_path}")
    typer.echo(f"queued_manifest: {report.queued_manifest_path}")
    typer.echo(f"queue_depth: {report.queue_depth}")
    typer.echo(f"overwritten: {'yes' if report.overwritten else 'no'}")


@closeout_app.command("process-inbox")
def closeout_process_inbox(
    root: str = typer.Argument(".", help="Workspace root used for federation discovery."),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the inbox directory."),
    processed_dir: str | None = typer.Option(
        None, "--processed-dir", help="Override the processed-manifest directory."
    ),
    failed_dir: str | None = typer.Option(None, "--failed-dir", help="Override the failed-manifest directory."),
    report_dir: str | None = typer.Option(None, "--report-dir", help="Override the closeout report directory."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.process_inbox(
        inbox_dir=inbox_dir,
        processed_dir=processed_dir,
        failed_dir=failed_dir,
        report_dir=report_dir,
    )
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        typer.echo(f"inbox: {report.inbox_dir}")
        typer.echo(f"processed: {report.processed_count}")
        typer.echo(f"failed: {report.failed_count}")
        for item in report.items:
            summary = item.archived_manifest_path or item.manifest_path
            typer.echo(f"{item.status}: {summary}")
            if item.report_path:
                typer.echo(f"  report: {item.report_path}")
            _print_kernel_next_brief(item.kernel_next_step_brief, indent="  ")
            _print_owner_follow_through(
                item.owner_follow_through_briefs,
                handoff_path=item.owner_handoff_path,
                indent="  ",
            )
            if item.error:
                typer.echo(f"  error: {item.error}")

    if report.failed_count:
        raise typer.Exit(code=1)


@closeout_app.command("status")
def closeout_status(
    root: str = typer.Argument(".", help="Workspace root used for federation discovery."),
    request_dir: str | None = typer.Option(None, "--request-dir", help="Override the request directory."),
    manifest_dir: str | None = typer.Option(None, "--manifest-dir", help="Override the built-manifest directory."),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the inbox directory."),
    processed_dir: str | None = typer.Option(
        None, "--processed-dir", help="Override the processed-manifest directory."
    ),
    failed_dir: str | None = typer.Option(None, "--failed-dir", help="Override the failed-manifest directory."),
    report_dir: str | None = typer.Option(None, "--report-dir", help="Override the closeout report directory."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.status(
        request_dir=request_dir,
        manifest_dir=manifest_dir,
        inbox_dir=inbox_dir,
        processed_dir=processed_dir,
        failed_dir=failed_dir,
        report_dir=report_dir,
    )
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"root: {report.root_dir}")
    typer.echo(f"requests: {report.request_dir}")
    typer.echo(f"manifests: {report.manifest_dir}")
    typer.echo(f"inbox: {report.inbox_dir}")
    typer.echo(f"review_requests: {report.request_count}")
    typer.echo(f"built_manifests: {report.manifest_count}")
    typer.echo(f"pending: {report.pending_manifest_count}")
    typer.echo(f"processed: {report.processed_manifest_count}")
    typer.echo(f"failed: {report.failed_manifest_count}")
    typer.echo(f"reports: {report.report_count}")
    typer.echo(f"handoffs: {report.handoff_count}")
    if report.latest_request_path:
        typer.echo(f"latest_request: {report.latest_request_path}")
    if report.latest_manifest_path:
        typer.echo(f"latest_manifest: {report.latest_manifest_path}")
    if report.latest_report_path:
        typer.echo(f"latest_report: {report.latest_report_path}")
    if report.latest_handoff_path:
        typer.echo(f"latest_handoff: {report.latest_handoff_path}")
    if report.latest_processed_manifest_path:
        typer.echo(f"latest_processed: {report.latest_processed_manifest_path}")
    if report.latest_failed_manifest_path:
        typer.echo(f"latest_failed: {report.latest_failed_manifest_path}")


if __name__ == "__main__":
    app()
