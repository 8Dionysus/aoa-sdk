from __future__ import annotations

from datetime import datetime, timezone

from ..workspace.discovery import Workspace
from .models import ChangeSignal, ConnectivityGap, ConnectivityGapReport
from .registry import RecurrenceRegistry, load_registry


def build_connectivity_gap_report(
    workspace: Workspace,
    *,
    signal: ChangeSignal | None = None,
    registry: RecurrenceRegistry | None = None,
) -> ConnectivityGapReport:
    registry = registry or load_registry(workspace)
    gaps: list[ConnectivityGap] = []
    gap_counter = 0

    for loaded in registry.iter_components():
        component = loaded.component

        if component.generated_surfaces and not component.source_inputs:
            gap_counter += 1
            gaps.append(
                ConnectivityGap(
                    gap_ref=f"gap:{gap_counter:03d}",
                    severity="high",
                    gap_kind="orphan_generated_surface",
                    component_ref=component.component_ref,
                    owner_repo=component.owner_repo,
                    evidence_refs=list(component.generated_surfaces),
                    recommendation="declare at least one source input for every generated surface family",
                )
            )

        if component.projected_surfaces and not component.generated_surfaces:
            gap_counter += 1
            gaps.append(
                ConnectivityGap(
                    gap_ref=f"gap:{gap_counter:03d}",
                    severity="medium",
                    gap_kind="projected_without_generation",
                    component_ref=component.component_ref,
                    owner_repo=component.owner_repo,
                    evidence_refs=list(component.projected_surfaces),
                    recommendation="name the repo-owned generated seam that feeds this projected surface",
                )
            )

        if component.generated_surfaces and not component.proof_surfaces:
            gap_counter += 1
            gaps.append(
                ConnectivityGap(
                    gap_ref=f"gap:{gap_counter:03d}",
                    severity="medium",
                    gap_kind="missing_proof_surface",
                    component_ref=component.component_ref,
                    owner_repo=component.owner_repo,
                    evidence_refs=list(component.generated_surfaces),
                    recommendation="attach at least one validator or doctor command to every generated surface family",
                )
            )

        if not component.refresh_routes:
            gap_counter += 1
            gaps.append(
                ConnectivityGap(
                    gap_ref=f"gap:{gap_counter:03d}",
                    severity="medium",
                    gap_kind="missing_refresh_route",
                    component_ref=component.component_ref,
                    owner_repo=component.owner_repo,
                    evidence_refs=[str(loaded.manifest_path.relative_to(loaded.manifest_path.parents[2]))],
                    recommendation="plant at least one explicit refresh route so recurrence can plan honestly",
                )
            )

        for edge in component.consumer_edges:
            if edge.target.startswith("component:") and registry.get(edge.target) is None:
                gap_counter += 1
                gaps.append(
                    ConnectivityGap(
                        gap_ref=f"gap:{gap_counter:03d}",
                        severity="medium" if edge.required else "low",
                        gap_kind="unresolved_edge",
                        component_ref=component.component_ref,
                        owner_repo=component.owner_repo,
                        evidence_refs=[edge.target],
                        recommendation="plant the target component manifest or weaken the edge until the target exists",
                    )
                )
                continue

            if edge.target_repo is not None:
                target_repo_has_manifests = any(
                    item.component.owner_repo == edge.target_repo for item in registry.iter_components()
                )
                if not target_repo_has_manifests:
                    gap_counter += 1
                    gaps.append(
                        ConnectivityGap(
                            gap_ref=f"gap:{gap_counter:03d}",
                            severity="low",
                            gap_kind="weak_owner_handoff",
                            component_ref=component.component_ref,
                            owner_repo=component.owner_repo,
                            evidence_refs=[f"{edge.target_repo}:{edge.target}"],
                            recommendation="plant a recurrence manifest in the target repo to close this owner boundary",
                        )
                    )

            needs_target_route = edge.kind in {"routes_via", "summarized_by", "donates_to_kag", "requires_regrounding"}
            if needs_target_route and not edge.suggested_commands:
                gap_counter += 1
                gaps.append(
                    ConnectivityGap(
                        gap_ref=f"gap:{gap_counter:03d}",
                        severity="medium",
                        gap_kind="missing_target_route",
                        component_ref=component.component_ref,
                        owner_repo=component.owner_repo,
                        evidence_refs=[f"{edge.target_repo or '?'}:{edge.target}"],
                        recommendation="declare the owner-repo route commands or land the target manifest that owns them",
                    )
                )

    if signal is not None:
        for path in signal.unmatched_paths:
            gap_counter += 1
            gaps.append(
                ConnectivityGap(
                    gap_ref=f"gap:{gap_counter:03d}",
                    severity="medium",
                    gap_kind="unmapped_changed_path",
                    evidence_refs=[f"{signal.repo_name}:{path}"],
                    recommendation="either map this path into a component manifest or make the path explicitly non-recurrent",
                )
            )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ConnectivityGapReport(
        report_ref=f"doctor:{stamp}",
        workspace_root=str(workspace.federation_root),
        signal_ref=signal.signal_ref if signal is not None else None,
        components_checked=sorted(item.component.component_ref for item in registry.iter_components()),
        gaps=gaps,
    )
