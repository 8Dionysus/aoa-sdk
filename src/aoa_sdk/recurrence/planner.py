from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

from ..workspace.discovery import Workspace
from .graph import classify_edge_strength, expand_component_graph
from .models import (
    ChangeSignal,
    PlanStep,
    PropagationBatch,
    PropagationPlan,
    RouteClass,
    SurfaceClass,
)
from .registry import RecurrenceRegistry, load_registry


PREFERRED_ACTIONS_BY_SURFACE_CLASS: dict[SurfaceClass, list[RouteClass]] = {
    "source": [
        "regenerate",
        "reexport",
        "rebuild",
        "reproject",
        "repair",
        "revalidate",
    ],
    "generated": ["repair", "regenerate", "rebuild", "revalidate"],
    "projected": ["reproject", "repair", "regenerate", "revalidate"],
    "contract": ["revalidate", "repair"],
    "docs": ["revalidate", "repair"],
    "test": ["revalidate", "repair"],
    "proof": ["revalidate", "repair"],
    "receipt": ["revalidate", "repair"],
    "other": ["repair", "revalidate"],
}

DEFAULT_ACTION_BY_EDGE_KIND: dict[str, RouteClass] = {
    "generates": "regenerate",
    "projects_to": "reproject",
    "validated_by": "revalidate",
    "documents": "repair",
    "evaluated_by": "revalidate",
    "routes_via": "reroute",
    "summarized_by": "restat",
    "donates_to_kag": "reground",
    "requires_regrounding": "reground",
    "handoff_home": "handoff",
    "owns": "repair",
}

RETURN_KIND_BY_ACTION: dict[RouteClass, "ReturnTargetKind"] = {
    "reroute": "route",
    "restat": "summary",
    "reground": "route",
    "handoff": "playbook",
    "reproject": "contract",
    "regenerate": "source",
    "reexport": "source",
    "rebuild": "source",
    "repair": "contract",
    "revalidate": "contract",
    "observe": "contract",
    "defer": "contract",
}


def build_propagation_plan(
    workspace: Workspace,
    *,
    signal: ChangeSignal,
    registry: RecurrenceRegistry | None = None,
    depth_limit: int = 8,
    include_optional_edges: bool = True,
) -> PropagationPlan:
    registry = registry or load_registry(workspace)
    direct_refs = _unique([item.component_ref for item in signal.direct_components])
    expansion = expand_component_graph(
        direct_component_refs=direct_refs,
        registry=registry,
        depth_limit=depth_limit,
        include_optional=include_optional_edges,
    )

    steps: list[PlanStep] = []
    step_counter = 0
    step_ref_by_component: dict[str, str] = {}
    extra_unresolved_edges: list[str] = []

    direct_matches_by_ref: dict[str, list[SurfaceClass]] = {}
    for item in signal.direct_components:
        direct_matches_by_ref.setdefault(item.component_ref, []).append(
            item.match_class
        )

    for node in expansion.component_nodes:
        loaded = registry.get(node.component_ref)
        if loaded is None:
            continue
        component = loaded.component
        action = choose_component_action(
            component_ref=component.component_ref,
            match_classes=direct_matches_by_ref.get(component.component_ref, []),
            incoming_action=node.via_edge.suggested_action
            if node.via_edge is not None
            else None,
            registry=registry,
        )
        commands = resolve_component_commands(
            component_ref=component.component_ref,
            action=action,
            registry=registry,
        )
        reason = build_component_reason(
            component_ref=component.component_ref,
            match_classes=direct_matches_by_ref.get(component.component_ref, []),
            parent_component_ref=node.parent_component_ref,
            incoming_edge_kind=node.via_edge.kind
            if node.via_edge is not None
            else None,
        )
        surface_refs = primary_surface_refs(component)
        depends_on = []
        if (
            node.parent_component_ref is not None
            and node.parent_component_ref in step_ref_by_component
        ):
            depends_on.append(step_ref_by_component[node.parent_component_ref])
        step_counter += 1
        step_ref = f"step:{step_counter:03d}:{component.owner_repo}"
        step = PlanStep(
            step_ref=step_ref,
            order=step_counter,
            component_ref=component.component_ref,
            owner_repo=component.owner_repo,
            action=action,
            reason=reason,
            surface_refs=surface_refs,
            commands=commands,
            depends_on=depends_on,
            review_required=True,
            status="planned" if commands or action == "handoff" else "blocked",
            batch_order=node.depth,
            graph_depth=node.depth,
            edge_strength=node.edge_strength,
        )
        steps.append(step)
        step_ref_by_component[component.component_ref] = step_ref

    for external in expansion.external_impacts:
        source_step_ref = step_ref_by_component.get(external.source_component_ref)
        source_loaded = registry.get(external.source_component_ref)
        if external.edge.target_repo is not None:
            owner_repo = external.edge.target_repo
        elif source_loaded is not None:
            owner_repo = source_loaded.component.owner_repo
        else:
            extra_unresolved_edges.append(
                f"{external.source_component_ref} could not resolve owner for edge {external.edge.kind}:{external.edge.target}"
            )
            continue
        action = external.edge.suggested_action or DEFAULT_ACTION_BY_EDGE_KIND.get(
            external.edge.kind, "repair"
        )
        commands = list(external.edge.suggested_commands)
        target_ref = external.edge.target
        step_counter += 1
        step_ref = f"step:{step_counter:03d}:{owner_repo}"
        status: Literal["planned", "blocked"] = (
            "planned" if commands or action == "handoff" else "blocked"
        )
        steps.append(
            PlanStep(
                step_ref=step_ref,
                order=step_counter,
                component_ref=target_ref
                if target_ref.startswith("component:")
                else f"{owner_repo}:{target_ref}",
                owner_repo=owner_repo,
                action=action,
                reason=f"{external.edge.kind} edge from {external.source_component_ref}",
                surface_refs=[target_ref],
                commands=commands,
                depends_on=[source_step_ref] if source_step_ref is not None else [],
                review_required=True,
                status=status,
                batch_order=external.depth,
                graph_depth=external.depth,
                edge_strength=classify_edge_strength(external.edge),
            )
        )

    unresolved_edges = list(expansion.unresolved_edges) + extra_unresolved_edges
    open_questions = []
    for cycle in expansion.cycles:
        open_questions.append(
            f"cycle detected: {' -> '.join(cycle.path)} via {cycle.edge_kind}"
        )
    for skipped in expansion.skipped_edges:
        open_questions.append(skipped)
    for step in steps:
        if step.status == "blocked":
            open_questions.append(
                f"{step.component_ref} has no planted route commands for {step.action}"
            )

    impacted_components = [
        node.component_ref
        for node in expansion.component_nodes
        if node.component_ref.startswith("component:")
    ]
    impacted_targets = _unique(
        impacted_components
        + [
            step.component_ref
            for step in steps
            if step.component_ref not in impacted_components
        ]
    )
    propagation_batches = build_plan_batches(steps)
    summary = (
        f"{len(direct_refs)} direct component(s), "
        f"{len(steps)} step(s), "
        f"{len(propagation_batches)} batch(es), "
        f"{len(unresolved_edges)} unresolved edge(s), "
        f"{len(expansion.cycles)} cycle(s), "
        f"{len(open_questions)} open question(s)"
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return PropagationPlan(
        plan_ref=f"plan:{stamp}:{signal.repo_name or 'workspace'}",
        signal_ref=signal.signal_ref,
        workspace_root=signal.workspace_root,
        direct_components=direct_refs,
        impacted_components=impacted_components,
        impacted_targets=impacted_targets,
        ordered_steps=steps,
        unresolved_edges=unresolved_edges,
        open_questions=open_questions,
        graph_closure_ref=f"graph-closure:{stamp}:{signal.repo_name or 'workspace'}",
        propagation_batches=propagation_batches,
        summary=summary,
    )


def build_plan_batches(steps: list[PlanStep]) -> list[PropagationBatch]:
    step_refs_by_batch: dict[int, list[str]] = defaultdict(list)
    dependencies_by_batch: dict[int, set[int]] = defaultdict(set)
    batch_by_step_ref = {step.step_ref: step.batch_order for step in steps}
    for step in steps:
        step_refs_by_batch[step.batch_order].append(step.step_ref)
        for dependency in step.depends_on:
            dependency_batch = batch_by_step_ref.get(dependency)
            if dependency_batch is not None and dependency_batch != step.batch_order:
                dependencies_by_batch[step.batch_order].add(dependency_batch)
    batches: list[PropagationBatch] = []
    for order in sorted(step_refs_by_batch):
        batches.append(
            PropagationBatch(
                batch_ref=f"batch:{order:03d}",
                order=order,
                step_refs=step_refs_by_batch[order],
                depends_on_batch_refs=[
                    f"batch:{value:03d}"
                    for value in sorted(dependencies_by_batch[order])
                ],
                rationale="direct changes"
                if order == 0
                else f"graph depth {order} closure",
            )
        )
    return batches


def choose_component_action(
    *,
    component_ref: str,
    match_classes: list[SurfaceClass],
    incoming_action: RouteClass | None,
    registry: RecurrenceRegistry,
) -> RouteClass:
    loaded = registry.get(component_ref)
    if loaded is None:
        return incoming_action or "repair"

    component = loaded.component
    available = {route.action for route in component.refresh_routes}

    if incoming_action is not None and incoming_action in available:
        return incoming_action

    if incoming_action is not None and not available:
        return incoming_action

    ordered_match_classes = match_classes or ["source"]
    for match_class in ordered_match_classes:
        for candidate in PREFERRED_ACTIONS_BY_SURFACE_CLASS[match_class]:
            if candidate in available:
                return candidate

    if component.refresh_routes:
        return component.refresh_routes[0].action
    return "repair"


def resolve_component_commands(
    *,
    component_ref: str,
    action: RouteClass,
    registry: RecurrenceRegistry,
) -> list[str]:
    loaded = registry.get(component_ref)
    if loaded is None:
        return []
    component = loaded.component
    for route in component.refresh_routes:
        if route.action == action:
            return list(route.commands)
    return list(component.proof_surfaces)


def build_component_reason(
    *,
    component_ref: str,
    match_classes: list[SurfaceClass],
    parent_component_ref: str | None,
    incoming_edge_kind: str | None,
) -> str:
    if parent_component_ref and incoming_edge_kind:
        return f"{incoming_edge_kind} propagation from {parent_component_ref}"
    if match_classes:
        joined = ", ".join(match_classes)
        return f"direct {joined} change detected for {component_ref}"
    return f"indirect propagation into {component_ref}"


def primary_surface_refs(component) -> list[str]:
    for candidate in (
        component.source_inputs,
        component.contract_surfaces,
        component.generated_surfaces,
        component.projected_surfaces,
        component.documentation_surfaces,
    ):
        if candidate:
            return list(candidate[:2])
    return []


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


ReturnTargetKind = Literal["source", "contract", "docs", "route", "summary", "playbook"]
