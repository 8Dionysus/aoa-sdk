from __future__ import annotations

from datetime import datetime, timezone

from ..workspace.discovery import Workspace
from .graph import expand_component_graph
from .models import ChangeSignal, PlanStep, PropagationPlan, RouteClass, SurfaceClass
from .registry import RecurrenceRegistry, load_registry


PREFERRED_ACTIONS_BY_SURFACE_CLASS: dict[SurfaceClass, list[RouteClass]] = {
    "source": ["regenerate", "reexport", "rebuild", "reproject", "repair", "revalidate"],
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

RETURN_KIND_BY_ACTION: dict[RouteClass, str] = {
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
) -> PropagationPlan:
    registry = registry or load_registry(workspace)
    direct_refs = _unique([item.component_ref for item in signal.direct_components])
    expansion = expand_component_graph(direct_component_refs=direct_refs, registry=registry)

    steps: list[PlanStep] = []
    step_counter = 0
    step_ref_by_component: dict[str, str] = {}

    direct_matches_by_ref: dict[str, list[SurfaceClass]] = {}
    for item in signal.direct_components:
        direct_matches_by_ref.setdefault(item.component_ref, []).append(item.match_class)

    for node in expansion.component_nodes:
        loaded = registry.get(node.component_ref)
        if loaded is None:
            continue
        component = loaded.component
        action = choose_component_action(
            component_ref=component.component_ref,
            match_classes=direct_matches_by_ref.get(component.component_ref, []),
            incoming_action=node.via_edge.suggested_action if node.via_edge is not None else None,
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
            incoming_edge_kind=node.via_edge.kind if node.via_edge is not None else None,
        )
        surface_refs = primary_surface_refs(component)
        depends_on = []
        if node.parent_component_ref is not None and node.parent_component_ref in step_ref_by_component:
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
        )
        steps.append(step)
        step_ref_by_component[component.component_ref] = step_ref

    for external in expansion.external_impacts:
        source_step_ref = step_ref_by_component.get(external.source_component_ref)
        owner_repo = external.edge.target_repo or registry.get(external.source_component_ref).component.owner_repo
        action = external.edge.suggested_action or DEFAULT_ACTION_BY_EDGE_KIND.get(external.edge.kind, "repair")
        commands = list(external.edge.suggested_commands)
        target_ref = external.edge.target
        step_counter += 1
        step_ref = f"step:{step_counter:03d}:{owner_repo}"
        status = "planned" if commands or action == "handoff" else "blocked"
        steps.append(
            PlanStep(
                step_ref=step_ref,
                order=step_counter,
                component_ref=target_ref if target_ref.startswith("component:") else f"{owner_repo}:{target_ref}",
                owner_repo=owner_repo,
                action=action,
                reason=f"{external.edge.kind} edge from {external.source_component_ref}",
                surface_refs=[target_ref],
                commands=commands,
                depends_on=[source_step_ref] if source_step_ref is not None else [],
                review_required=True,
                status=status,
            )
        )

    unresolved_edges = list(expansion.unresolved_edges)
    open_questions = []
    for step in steps:
        if step.status == "blocked":
            open_questions.append(f"{step.component_ref} has no planted route commands for {step.action}")

    impacted_components = [
        node.component_ref for node in expansion.component_nodes if node.component_ref.startswith("component:")
    ]
    impacted_targets = _unique(
        impacted_components + [step.component_ref for step in steps if step.component_ref not in impacted_components]
    )
    summary = (
        f"{len(direct_refs)} direct component(s), "
        f"{len(steps)} step(s), "
        f"{len(unresolved_edges)} unresolved edge(s), "
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
        summary=summary,
    )


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
