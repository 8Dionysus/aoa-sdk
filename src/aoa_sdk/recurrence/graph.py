from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Literal

from pydantic import Field

from .models import ConsumerEdge, EdgeStrength, ManifestDiagnostic, StrictModel
from .registry import RecurrenceRegistry

EDGE_KIND_ORDER: dict[str, int] = {
    "owns": 0,
    "generates": 10,
    "projects_to": 20,
    "validated_by": 30,
    "documents": 40,
    "evaluated_by": 50,
    "routes_via": 60,
    "summarized_by": 70,
    "donates_to_kag": 80,
    "requires_regrounding": 90,
    "handoff_home": 100,
}

GraphTargetKind = Literal["component", "external"]
GraphDeltaKind = Literal["added", "removed", "changed"]


@dataclass(slots=True)
class ComponentTraversal:
    component_ref: str
    parent_component_ref: str | None
    via_edge: ConsumerEdge | None
    depth: int = 0
    lineage: tuple[str, ...] = ()
    edge_strength: EdgeStrength = "required"


@dataclass(slots=True)
class ExternalImpact:
    source_component_ref: str
    edge: ConsumerEdge
    depth: int = 0
    lineage: tuple[str, ...] = ()
    edge_strength: EdgeStrength = "required"


@dataclass(slots=True)
class CycleRecord:
    cycle_ref: str
    source_component_ref: str
    target_component_ref: str
    edge_kind: str
    path: list[str]
    depth: int


@dataclass(slots=True)
class GraphExpansion:
    component_nodes: list[ComponentTraversal]
    external_impacts: list[ExternalImpact]
    unresolved_edges: list[str]
    cycles: list[CycleRecord]
    skipped_edges: list[str]
    depth_limit: int
    max_depth_seen: int

    def propagation_batches(self) -> dict[int, list[str]]:
        batches: dict[int, list[str]] = defaultdict(list)
        for node in self.component_nodes:
            _append_unique(batches[node.depth], node.component_ref)
        for impact in self.external_impacts:
            label = f"{impact.edge.target_repo or 'external'}:{impact.edge.target}"
            _append_unique(batches[impact.depth], label)
        return {key: batches[key] for key in sorted(batches)}


class GraphClosureNode(StrictModel):
    component_ref: str
    owner_repo: str | None = None
    depth: int
    parent_component_ref: str | None = None
    via_edge_kind: str | None = None
    edge_strength: EdgeStrength = "required"
    lineage: list[str] = Field(default_factory=list)


class GraphClosureExternalImpact(StrictModel):
    source_component_ref: str
    target: str
    target_repo: str | None = None
    kind: str
    depth: int
    edge_strength: EdgeStrength = "required"
    suggested_action: str | None = None
    lineage: list[str] = Field(default_factory=list)


class GraphCycle(StrictModel):
    cycle_ref: str
    source_component_ref: str
    target_component_ref: str
    edge_kind: str
    path: list[str] = Field(default_factory=list)
    depth: int


class GraphPropagationBatch(StrictModel):
    batch_ref: str
    order: int
    component_refs: list[str] = Field(default_factory=list)
    external_targets: list[str] = Field(default_factory=list)
    rationale: str = ""


class GraphClosureReport(StrictModel):
    schema_version: Literal["aoa_graph_closure_report_v1"] = (
        "aoa_graph_closure_report_v1"
    )
    report_ref: str
    workspace_root: str
    direct_components: list[str] = Field(default_factory=list)
    depth_limit: int
    max_depth_seen: int
    nodes: list[GraphClosureNode] = Field(default_factory=list)
    external_impacts: list[GraphClosureExternalImpact] = Field(default_factory=list)
    cycles: list[GraphCycle] = Field(default_factory=list)
    unresolved_edges: list[str] = Field(default_factory=list)
    skipped_edges: list[str] = Field(default_factory=list)
    propagation_batches: list[GraphPropagationBatch] = Field(default_factory=list)


class GraphSnapshotNode(StrictModel):
    node_ref: str
    component_ref: str
    owner_repo: str
    description: str = ""
    surface_counts: dict[str, int] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class GraphSnapshotEdge(StrictModel):
    edge_ref: str
    source_component_ref: str
    source_owner_repo: str
    kind: str
    target: str
    target_repo: str | None = None
    target_kind: GraphTargetKind
    required: bool = True
    edge_strength: EdgeStrength = "required"
    suggested_action: str | None = None
    suggested_commands: list[str] = Field(default_factory=list)
    notes: str = ""


class GraphSnapshot(StrictModel):
    schema_version: Literal["aoa_graph_snapshot_v1"] = "aoa_graph_snapshot_v1"
    snapshot_ref: str
    workspace_root: str
    created_at: datetime
    node_count: int
    edge_count: int
    nodes: list[GraphSnapshotNode] = Field(default_factory=list)
    edges: list[GraphSnapshotEdge] = Field(default_factory=list)
    manifest_diagnostics: list[ManifestDiagnostic] = Field(default_factory=list)


class GraphDeltaItem(StrictModel):
    item_ref: str
    change_kind: GraphDeltaKind
    item_kind: Literal["node", "edge"]
    key: str
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    summary: str = ""


class GraphDeltaReport(StrictModel):
    schema_version: Literal["aoa_graph_delta_report_v1"] = "aoa_graph_delta_report_v1"
    report_ref: str
    workspace_root: str
    before_snapshot_ref: str
    after_snapshot_ref: str
    added_nodes: list[GraphDeltaItem] = Field(default_factory=list)
    removed_nodes: list[GraphDeltaItem] = Field(default_factory=list)
    added_edges: list[GraphDeltaItem] = Field(default_factory=list)
    removed_edges: list[GraphDeltaItem] = Field(default_factory=list)
    changed_edges: list[GraphDeltaItem] = Field(default_factory=list)
    summary: str = ""


def classify_edge_strength(edge: ConsumerEdge) -> EdgeStrength:
    notes = (edge.notes or "").lower()
    if "forbidden" in notes or "stop-line" in notes:
        return "forbidden"
    if edge.required:
        return "required"
    if edge.suggested_action == "defer":
        return "advisory"
    return "recommended"


def expand_component_graph(
    *,
    direct_component_refs: list[str],
    registry: RecurrenceRegistry,
    depth_limit: int = 8,
    include_optional: bool = True,
) -> GraphExpansion:
    direct_refs = _unique([value for value in direct_component_refs if value])
    queue: deque[ComponentTraversal] = deque(
        ComponentTraversal(
            component_ref=component_ref,
            parent_component_ref=None,
            via_edge=None,
            depth=0,
            lineage=(component_ref,),
            edge_strength="required",
        )
        for component_ref in direct_refs
    )
    seen_depth: dict[str, int] = {}
    component_nodes: list[ComponentTraversal] = []
    external_impacts: list[ExternalImpact] = []
    external_seen: set[str] = set()
    unresolved_edges: list[str] = []
    skipped_edges: list[str] = []
    cycles: list[CycleRecord] = []
    max_depth_seen = 0

    while queue:
        current = queue.popleft()
        max_depth_seen = max(max_depth_seen, current.depth)
        previous_depth = seen_depth.get(current.component_ref)
        if previous_depth is not None and previous_depth <= current.depth:
            continue
        seen_depth[current.component_ref] = current.depth
        component_nodes.append(current)

        loaded = registry.get(current.component_ref)
        if loaded is None:
            unresolved_edges.append(
                f"missing component manifest: {current.component_ref}"
            )
            continue

        for edge in _ordered_edges(loaded.component.consumer_edges):
            strength = classify_edge_strength(edge)
            if not include_optional and strength in {"recommended", "advisory"}:
                skipped_edges.append(
                    f"optional edge skipped: {loaded.component.component_ref} -> {edge.target} ({edge.kind})"
                )
                continue

            next_depth = current.depth + 1
            if edge.target.startswith("component:"):
                if edge.target in current.lineage:
                    path = [*current.lineage, edge.target]
                    cycles.append(
                        CycleRecord(
                            cycle_ref=f"cycle:{_short_hash('|'.join(path) + ':' + edge.kind)}",
                            source_component_ref=loaded.component.component_ref,
                            target_component_ref=edge.target,
                            edge_kind=edge.kind,
                            path=list(path),
                            depth=next_depth,
                        )
                    )
                    continue

                if next_depth > depth_limit:
                    unresolved_edges.append(
                        f"depth limit {depth_limit} reached: {loaded.component.component_ref} -> {edge.target} ({edge.kind})"
                    )
                    skipped_edges.append(
                        f"depth-limit edge skipped: {loaded.component.component_ref} -> {edge.target} ({edge.kind})"
                    )
                    continue

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
                        depth=next_depth,
                        lineage=(*current.lineage, target.component.component_ref),
                        edge_strength=strength,
                    )
                )
                continue

            impact_key = _edge_key(loaded.component.component_ref, edge)
            if impact_key in external_seen:
                continue
            external_seen.add(impact_key)
            external_impacts.append(
                ExternalImpact(
                    source_component_ref=loaded.component.component_ref,
                    edge=edge,
                    depth=next_depth,
                    lineage=current.lineage,
                    edge_strength=strength,
                )
            )

    reachable_refs = {item.component_ref for item in component_nodes}
    cycles.extend(
        _detect_reachable_cycles(
            reachable_refs, registry, existing={tuple(item.path) for item in cycles}
        )
    )

    component_nodes.sort(key=lambda item: (item.depth, item.component_ref))
    external_impacts.sort(
        key=lambda item: (
            item.depth,
            item.source_component_ref,
            item.edge.kind,
            item.edge.target,
        )
    )
    return GraphExpansion(
        component_nodes=component_nodes,
        external_impacts=external_impacts,
        unresolved_edges=_unique(unresolved_edges),
        cycles=cycles,
        skipped_edges=_unique(skipped_edges),
        depth_limit=depth_limit,
        max_depth_seen=max_depth_seen,
    )


def build_graph_closure_report(
    workspace: Any,
    *,
    direct_component_refs: list[str],
    registry: RecurrenceRegistry,
    depth_limit: int = 8,
    include_optional: bool = True,
) -> GraphClosureReport:
    expansion = expand_component_graph(
        direct_component_refs=direct_component_refs,
        registry=registry,
        depth_limit=depth_limit,
        include_optional=include_optional,
    )
    stamp = _stamp()
    nodes: list[GraphClosureNode] = []
    for item in expansion.component_nodes:
        loaded = registry.get(item.component_ref)
        nodes.append(
            GraphClosureNode(
                component_ref=item.component_ref,
                owner_repo=loaded.component.owner_repo if loaded is not None else None,
                depth=item.depth,
                parent_component_ref=item.parent_component_ref,
                via_edge_kind=item.via_edge.kind if item.via_edge is not None else None,
                edge_strength=item.edge_strength,
                lineage=list(item.lineage),
            )
        )
    external_impacts = [
        GraphClosureExternalImpact(
            source_component_ref=item.source_component_ref,
            target=item.edge.target,
            target_repo=item.edge.target_repo,
            kind=item.edge.kind,
            depth=item.depth,
            edge_strength=item.edge_strength,
            suggested_action=item.edge.suggested_action,
            lineage=list(item.lineage),
        )
        for item in expansion.external_impacts
    ]
    return GraphClosureReport(
        report_ref=f"graph-closure:{stamp}:{_short_hash('|'.join(_unique(direct_component_refs)))}",
        workspace_root=str(workspace.root),
        direct_components=_unique(direct_component_refs),
        depth_limit=expansion.depth_limit,
        max_depth_seen=expansion.max_depth_seen,
        nodes=nodes,
        external_impacts=external_impacts,
        cycles=[
            GraphCycle(
                cycle_ref=item.cycle_ref,
                source_component_ref=item.source_component_ref,
                target_component_ref=item.target_component_ref,
                edge_kind=item.edge_kind,
                path=item.path,
                depth=item.depth,
            )
            for item in expansion.cycles
        ],
        unresolved_edges=list(expansion.unresolved_edges),
        skipped_edges=list(expansion.skipped_edges),
        propagation_batches=_closure_batches(expansion),
    )


def build_graph_snapshot(
    workspace: Any,
    *,
    registry: RecurrenceRegistry,
    include_manifest_diagnostics: bool = True,
) -> GraphSnapshot:
    nodes: list[GraphSnapshotNode] = []
    edges: list[GraphSnapshotEdge] = []
    for loaded in sorted(
        registry.iter_components(), key=lambda item: item.component.component_ref
    ):
        component = loaded.component
        nodes.append(
            GraphSnapshotNode(
                node_ref=f"node:{component.component_ref}",
                component_ref=component.component_ref,
                owner_repo=component.owner_repo,
                description=component.description,
                surface_counts={
                    "source": len(component.source_inputs),
                    "generated": len(component.generated_surfaces),
                    "projected": len(component.projected_surfaces),
                    "contract": len(component.contract_surfaces),
                    "docs": len(component.documentation_surfaces),
                    "test": len(component.test_surfaces),
                    "proof": len(component.proof_surfaces),
                    "receipt": len(component.receipt_surfaces),
                    "refresh_routes": len(component.refresh_routes),
                    "consumer_edges": len(component.consumer_edges),
                },
                tags=list(component.tags),
            )
        )
        for edge in _ordered_edges(component.consumer_edges):
            edges.append(
                GraphSnapshotEdge(
                    edge_ref=_edge_ref(component.component_ref, edge),
                    source_component_ref=component.component_ref,
                    source_owner_repo=component.owner_repo,
                    kind=edge.kind,
                    target=edge.target,
                    target_repo=edge.target_repo,
                    target_kind="component"
                    if edge.target.startswith("component:")
                    else "external",
                    required=edge.required,
                    edge_strength=classify_edge_strength(edge),
                    suggested_action=edge.suggested_action,
                    suggested_commands=list(edge.suggested_commands),
                    notes=edge.notes,
                )
            )
    edges.sort(
        key=lambda item: (
            item.source_component_ref,
            EDGE_KIND_ORDER.get(item.kind, 999),
            item.target,
        )
    )
    diagnostics = (
        list(registry.iter_manifest_diagnostics())
        if include_manifest_diagnostics
        else []
    )
    stamp = _stamp()
    return GraphSnapshot(
        snapshot_ref=f"graph-snapshot:{stamp}:{_short_hash(str(workspace.root) + str(len(nodes)) + str(len(edges)))}",
        workspace_root=str(workspace.root),
        created_at=datetime.now(timezone.utc),
        node_count=len(nodes),
        edge_count=len(edges),
        nodes=nodes,
        edges=edges,
        manifest_diagnostics=diagnostics,
    )


def diff_graph_snapshots(
    before: GraphSnapshot, after: GraphSnapshot
) -> GraphDeltaReport:
    before_nodes = {item.node_ref: item for item in before.nodes}
    after_nodes = {item.node_ref: item for item in after.nodes}
    before_edges = {_snapshot_edge_key(item): item for item in before.edges}
    after_edges = {_snapshot_edge_key(item): item for item in after.edges}

    added_nodes = [
        _delta_item(
            "node",
            "added",
            key,
            None,
            after_nodes[key].model_dump(mode="json"),
            f"node added: {key}",
        )
        for key in sorted(set(after_nodes) - set(before_nodes))
    ]
    removed_nodes = [
        _delta_item(
            "node",
            "removed",
            key,
            before_nodes[key].model_dump(mode="json"),
            None,
            f"node removed: {key}",
        )
        for key in sorted(set(before_nodes) - set(after_nodes))
    ]
    added_edges = [
        _delta_item(
            "edge",
            "added",
            key,
            None,
            after_edges[key].model_dump(mode="json"),
            f"edge added: {key}",
        )
        for key in sorted(set(after_edges) - set(before_edges))
    ]
    removed_edges = [
        _delta_item(
            "edge",
            "removed",
            key,
            before_edges[key].model_dump(mode="json"),
            None,
            f"edge removed: {key}",
        )
        for key in sorted(set(before_edges) - set(after_edges))
    ]
    changed_edges: list[GraphDeltaItem] = []
    for key in sorted(set(before_edges) & set(after_edges)):
        before_payload = before_edges[key].model_dump(mode="json")
        after_payload = after_edges[key].model_dump(mode="json")
        if before_payload != after_payload:
            changed_edges.append(
                _delta_item(
                    "edge",
                    "changed",
                    key,
                    before_payload,
                    after_payload,
                    f"edge changed: {key}",
                )
            )
    summary = (
        f"+{len(added_nodes)} node(s), -{len(removed_nodes)} node(s), "
        f"+{len(added_edges)} edge(s), -{len(removed_edges)} edge(s), "
        f"~{len(changed_edges)} changed edge(s)"
    )
    return GraphDeltaReport(
        report_ref=f"graph-delta:{_stamp()}:{_short_hash(before.snapshot_ref + after.snapshot_ref)}",
        workspace_root=after.workspace_root,
        before_snapshot_ref=before.snapshot_ref,
        after_snapshot_ref=after.snapshot_ref,
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        added_edges=added_edges,
        removed_edges=removed_edges,
        changed_edges=changed_edges,
        summary=summary,
    )


def _closure_batches(expansion: GraphExpansion) -> list[GraphPropagationBatch]:
    component_by_depth: dict[int, list[str]] = defaultdict(list)
    external_by_depth: dict[int, list[str]] = defaultdict(list)
    for node in expansion.component_nodes:
        _append_unique(component_by_depth[node.depth], node.component_ref)
    for impact in expansion.external_impacts:
        label = f"{impact.edge.target_repo or 'external'}:{impact.edge.target}"
        _append_unique(external_by_depth[impact.depth], label)
    orders = sorted(set(component_by_depth) | set(external_by_depth))
    return [
        GraphPropagationBatch(
            batch_ref=f"graph-batch:{order:03d}",
            order=order,
            component_refs=component_by_depth.get(order, []),
            external_targets=external_by_depth.get(order, []),
            rationale="direct change"
            if order == 0
            else f"depth {order} typed-edge propagation",
        )
        for order in orders
    ]


def _detect_reachable_cycles(
    reachable_refs: set[str],
    registry: RecurrenceRegistry,
    *,
    existing: set[tuple[str, ...]],
) -> list[CycleRecord]:
    cycles: list[CycleRecord] = []
    emitted: set[str] = {_cycle_signature(list(path)) for path in existing}

    def walk(
        component_ref: str, stack: list[str], edge_kind: str | None = None
    ) -> None:
        if component_ref in stack:
            start = stack.index(component_ref)
            path = [*stack[start:], component_ref]
            signature = _cycle_signature(path)
            if signature not in emitted:
                emitted.add(signature)
                cycles.append(
                    CycleRecord(
                        cycle_ref=f"cycle:{_short_hash('|'.join(path) + ':' + (edge_kind or 'edge'))}",
                        source_component_ref=stack[-1] if stack else component_ref,
                        target_component_ref=component_ref,
                        edge_kind=edge_kind or "edge",
                        path=path,
                        depth=len(path) - 1,
                    )
                )
            return
        if component_ref not in reachable_refs:
            return
        loaded = registry.get(component_ref)
        if loaded is None:
            return
        next_stack = [*stack, component_ref]
        for edge in _ordered_edges(loaded.component.consumer_edges):
            if edge.target.startswith("component:") and edge.target in reachable_refs:
                walk(edge.target, next_stack, edge.kind)

    for component_ref in sorted(reachable_refs):
        walk(component_ref, [])
    return cycles


def _cycle_signature(path: list[str]) -> str:
    if not path:
        return ""
    core = path[:-1] if path[0] == path[-1] else path
    if not core:
        return ""
    rotations = [tuple(core[index:] + core[:index]) for index in range(len(core))]
    canonical = min(rotations)
    return "|".join(canonical)


def _ordered_edges(edges: list[ConsumerEdge]) -> list[ConsumerEdge]:
    return sorted(
        edges,
        key=lambda edge: (
            EDGE_KIND_ORDER.get(edge.kind, 999),
            0 if edge.required else 1,
            edge.target_repo or "",
            edge.target,
        ),
    )


def _edge_key(source_component_ref: str, edge: ConsumerEdge) -> str:
    return f"{source_component_ref}|{edge.kind}|{edge.target_repo or ''}|{edge.target}"


def _snapshot_edge_key(edge: GraphSnapshotEdge) -> str:
    return f"{edge.source_component_ref}|{edge.kind}|{edge.target_repo or ''}|{edge.target}"


def _edge_ref(source_component_ref: str, edge: ConsumerEdge) -> str:
    return f"edge:{_short_hash(_edge_key(source_component_ref, edge))}"


def _delta_item(
    item_kind: Literal["node", "edge"],
    change_kind: GraphDeltaKind,
    key: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    summary: str,
) -> GraphDeltaItem:
    return GraphDeltaItem(
        item_ref=f"graph-delta-item:{_short_hash(item_kind + ':' + change_kind + ':' + key)}",
        change_kind=change_kind,
        item_kind=item_kind,
        key=key,
        before=before,
        after=after,
        summary=summary,
    )


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _short_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:16]


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
