from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from .models import PropagationPlan, RecurrenceComponent, ReturnHandoff, ReturnTarget
from .registry import RecurrenceRegistry
from .planner import RETURN_KIND_BY_ACTION

ReturnTargetKind = Literal["source", "contract", "docs", "route", "summary", "playbook"]


def build_return_handoff(
    *,
    plan: PropagationPlan,
    registry: RecurrenceRegistry,
    reviewed: bool = True,
) -> ReturnHandoff:
    if not reviewed:
        raise ValueError("return handoff requires reviewed=True")

    targets: list[ReturnTarget] = []
    seen: set[tuple[str, str | None, str]] = set()

    for component_ref in plan.direct_components:
        loaded = registry.get(component_ref)
        if loaded is None:
            continue
        component = loaded.component
        primary_target, target_kind = choose_primary_return_target(component)
        add_target(
            targets,
            seen,
            ReturnTarget(
                owner_repo=component.owner_repo,
                component_ref=component.component_ref,
                target=primary_target,
                target_kind=target_kind,
                reason="smallest owner-boundary re-entry surface for the direct component",
            ),
        )
        if component.rollback_anchors:
            add_target(
                targets,
                seen,
                ReturnTarget(
                    owner_repo=component.owner_repo,
                    component_ref=component.component_ref,
                    target=component.rollback_anchors[0],
                    target_kind="docs",
                    reason="first rollback anchor preserved for bounded recovery",
                ),
            )

    for step in plan.ordered_steps:
        if step.owner_repo in {target.owner_repo for target in targets if target.owner_repo == step.owner_repo}:
            pass
        if step.action in {"reroute", "restat", "reground", "handoff"}:
            add_target(
                targets,
                seen,
                ReturnTarget(
                    owner_repo=step.owner_repo,
                    component_ref=step.component_ref if step.component_ref.startswith("component:") else None,
                    target=step.surface_refs[0] if step.surface_refs else step.component_ref,
                    target_kind=RETURN_KIND_BY_ACTION[step.action],
                    reason=f"{step.action} downstream surface preserved for reviewed follow-through",
                ),
            )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ReturnHandoff(
        handoff_ref=f"handoff:{stamp}",
        plan_ref=plan.plan_ref,
        reviewed=True,
        surviving_fields=[
            "component_ref",
            "owner_repo",
            "action",
            "surface_refs",
            "reason",
            "review_required",
            "rollback_anchor",
        ],
        targets=targets,
        unresolved_items=list(plan.unresolved_edges) + list(plan.open_questions),
    )


def choose_primary_return_target(component: RecurrenceComponent) -> tuple[str, ReturnTargetKind]:
    if component.contract_surfaces:
        return component.contract_surfaces[0], "contract"
    if component.source_inputs:
        return component.source_inputs[0], "source"
    if component.documentation_surfaces:
        return component.documentation_surfaces[0], "docs"
    if component.generated_surfaces:
        return component.generated_surfaces[0], "docs"
    return component.component_ref, "docs"


def add_target(
    targets: list[ReturnTarget],
    seen: set[tuple[str, str | None, str]],
    target: ReturnTarget,
) -> None:
    key = (target.owner_repo, target.component_ref, target.target)
    if key in seen:
        return
    seen.add(key)
    targets.append(target)
