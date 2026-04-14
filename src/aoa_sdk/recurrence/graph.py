from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .models import ConsumerEdge
from .registry import RecurrenceRegistry


@dataclass(slots=True)
class ComponentTraversal:
    component_ref: str
    parent_component_ref: str | None
    via_edge: ConsumerEdge | None


@dataclass(slots=True)
class ExternalImpact:
    source_component_ref: str
    edge: ConsumerEdge


@dataclass(slots=True)
class GraphExpansion:
    component_nodes: list[ComponentTraversal]
    external_impacts: list[ExternalImpact]
    unresolved_edges: list[str]


def expand_component_graph(
    *,
    direct_component_refs: list[str],
    registry: RecurrenceRegistry,
) -> GraphExpansion:
    queue: deque[ComponentTraversal] = deque(
        ComponentTraversal(component_ref=component_ref, parent_component_ref=None, via_edge=None)
        for component_ref in direct_component_refs
    )
    seen: set[str] = set()
    component_nodes: list[ComponentTraversal] = []
    external_impacts: list[ExternalImpact] = []
    unresolved_edges: list[str] = []

    while queue:
        current = queue.popleft()
        if current.component_ref in seen:
            continue
        seen.add(current.component_ref)
        component_nodes.append(current)
        loaded = registry.get(current.component_ref)
        if loaded is None:
            unresolved_edges.append(f"missing component manifest: {current.component_ref}")
            continue

        for edge in loaded.component.consumer_edges:
            if edge.target.startswith("component:"):
                target = registry.get(edge.target)
                if target is None:
                    unresolved_edges.append(
                        f"{loaded.component.component_ref} -> {edge.target} ({edge.kind}) is not planted"
                    )
                    continue
                queue.append(
                    ComponentTraversal(
                        component_ref=target.component.component_ref,
                        parent_component_ref=loaded.component.component_ref,
                        via_edge=edge,
                    )
                )
                continue
            external_impacts.append(
                ExternalImpact(source_component_ref=loaded.component.component_ref, edge=edge)
            )

    return GraphExpansion(
        component_nodes=component_nodes,
        external_impacts=external_impacts,
        unresolved_edges=unresolved_edges,
    )
