from __future__ import annotations

from pathlib import Path

from ..workspace.discovery import Workspace
from .beacons import build_beacon_packet
from .decisions import (
    build_owner_review_decision_template,
    close_review_decisions,
    load_decisions_from_paths,
)
from .detector import detect_change_signal
from .doctor import build_connectivity_gap_report
from .graph import (
    GraphClosureReport,
    GraphDeltaReport,
    GraphSnapshot,
    build_graph_closure_report,
    build_graph_snapshot,
    diff_graph_snapshots,
)
from .hook_registry import HookRegistry, load_hook_registry
from .hooks import build_hook_run_report, list_hook_bindings
from .io import read_model
from .live_observations import build_live_observation_packet, list_live_producers
from .ledger import build_candidate_ledger
from .models import (
    BeaconPacket,
    CandidateDossierPacket,
    CandidateLedger,
    ChangeSignal,
    ConnectivityGapReport,
    DownstreamProjectionBundle,
    DownstreamProjectionGuardReport,
    HookBinding,
    HookEvent,
    HookRunReport,
    ManifestScanReport,
    ObservationPacket,
    OwnerReviewDecision,
    OwnerReviewSummary,
    PropagationPlan,
    RecurrenceKagProjection,
    RecurrenceRoutingProjection,
    RecurrenceStatsProjection,
    ReviewDecisionAction,
    ReviewDecisionCloseReport,
    ReturnHandoff,
    ReviewQueue,
    RolloutWindowBundle,
    UsageGapReport,
    WiringPlan,
)
from .observations import build_observation_packet
from .planner import build_propagation_plan
from .projections import (
    build_downstream_projection_bundle,
    build_kag_projection,
    build_projection_guard_report,
    build_routing_projection,
    build_stats_projection,
)
from .reentry import build_return_handoff
from .registry import RecurrenceRegistry, build_manifest_scan_report, load_registry
from .review import (
    build_candidate_dossier_packet,
    build_owner_review_summary,
    build_review_queue,
)
from .rollout import build_rollout_window_bundle
from .usage_gaps import build_usage_gap_report
from .wiring import build_wiring_plan


class RecurrenceAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def registry(self) -> RecurrenceRegistry:
        return load_registry(self.workspace)

    def _loaded_component_refs(self) -> list[str]:
        return [
            loaded.component.component_ref
            for loaded in self.registry().iter_components()
        ]

    def manifest_scan(self) -> ManifestScanReport:
        registry = self.registry()
        return build_manifest_scan_report(self.workspace, registry=registry)

    def hook_registry(self) -> HookRegistry:
        return load_hook_registry(self.workspace)

    def hooks(self, *, event: HookEvent | None = None) -> list[HookBinding]:
        return list_hook_bindings(
            self.workspace, event=event, registry=self.hook_registry()
        )

    def run_hooks(
        self,
        *,
        event: HookEvent,
        signal_or_path: ChangeSignal | str | Path | None = None,
        binding_refs: list[str] | None = None,
    ) -> HookRunReport:
        signal = None
        if isinstance(signal_or_path, (str, Path)):
            signal = read_model(signal_or_path, ChangeSignal)
        elif isinstance(signal_or_path, ChangeSignal):
            signal = signal_or_path
        return build_hook_run_report(
            self.workspace,
            event=event,
            signal=signal,
            registry=self.hook_registry(),
            recurrence_registry=self.registry(),
            binding_refs=binding_refs,
        )

    def detect(
        self,
        *,
        repo_root: str,
        diff_base: str | None = None,
        paths: list[str] | None = None,
    ) -> ChangeSignal:
        return detect_change_signal(
            self.workspace,
            repo_root=repo_root,
            diff_base=diff_base,
            paths=paths,
            registry=self.registry(),
        )

    def plan(self, report_or_path: ChangeSignal | str | Path) -> PropagationPlan:
        if isinstance(report_or_path, (str, Path)):
            report = read_model(report_or_path, ChangeSignal)
        else:
            report = report_or_path
        return build_propagation_plan(
            self.workspace, signal=report, registry=self.registry()
        )

    def doctor(
        self,
        report_or_path: ChangeSignal | str | Path | None = None,
        *,
        include_manifest_diagnostics: bool = True,
    ) -> ConnectivityGapReport:
        report = None
        if isinstance(report_or_path, (str, Path)):
            report = read_model(report_or_path, ChangeSignal)
        elif isinstance(report_or_path, ChangeSignal):
            report = report_or_path
        return build_connectivity_gap_report(
            self.workspace,
            signal=report,
            registry=self.registry(),
            include_manifest_diagnostics=include_manifest_diagnostics,
        )

    def build_return_handoff(
        self,
        plan_or_path: PropagationPlan | str | Path,
        *,
        reviewed: bool = True,
    ) -> ReturnHandoff:
        if isinstance(plan_or_path, (str, Path)):
            plan = read_model(plan_or_path, PropagationPlan)
        else:
            plan = plan_or_path
        return build_return_handoff(
            plan=plan, registry=self.registry(), reviewed=reviewed
        )

    def live_producers(self) -> list[str]:
        return list_live_producers()

    def live_observations(
        self,
        *,
        producers: list[str] | None = None,
        max_observations_per_producer: int = 200,
    ) -> ObservationPacket:
        return build_live_observation_packet(
            self.workspace,
            registry=self.registry(),
            producers=producers,
            max_observations_per_producer=max_observations_per_producer,
        )

    def observe(
        self,
        signal_or_path: ChangeSignal | str | Path | None = None,
        *,
        supplemental_paths: list[str] | None = None,
        hook_run_paths: list[str] | None = None,
    ) -> ObservationPacket:
        signal = None
        if isinstance(signal_or_path, (str, Path)):
            signal = read_model(signal_or_path, ChangeSignal)
        elif isinstance(signal_or_path, ChangeSignal):
            signal = signal_or_path
        return build_observation_packet(
            self.workspace,
            signal=signal,
            registry=self.registry(),
            supplemental_paths=supplemental_paths,
            hook_run_paths=hook_run_paths,
        )

    def beacon(
        self, observation_or_path: ObservationPacket | str | Path
    ) -> BeaconPacket:
        if isinstance(observation_or_path, (str, Path)):
            packet = read_model(observation_or_path, ObservationPacket)
        else:
            packet = observation_or_path
        return build_beacon_packet(
            self.workspace, observations=packet, registry=self.registry()
        )

    def ledger(
        self,
        beacon_or_path: BeaconPacket | str | Path,
        *,
        include_lower_status: bool = True,
    ) -> CandidateLedger:
        if isinstance(beacon_or_path, (str, Path)):
            packet = read_model(beacon_or_path, BeaconPacket)
        else:
            packet = beacon_or_path
        return build_candidate_ledger(packet, include_lower_status=include_lower_status)

    def usage_gaps(self, beacon_or_path: BeaconPacket | str | Path) -> UsageGapReport:
        if isinstance(beacon_or_path, (str, Path)):
            packet = read_model(beacon_or_path, BeaconPacket)
        else:
            packet = beacon_or_path
        return build_usage_gap_report(packet)

    def review_queue(
        self,
        beacon_or_path: BeaconPacket | str | Path,
        *,
        usage_gap_or_path: UsageGapReport | str | Path | None = None,
        include_lower_status: bool = False,
        include_watch_usage_gaps: bool = True,
    ) -> ReviewQueue:
        if isinstance(beacon_or_path, (str, Path)):
            packet = read_model(beacon_or_path, BeaconPacket)
        else:
            packet = beacon_or_path
        usage_gaps: UsageGapReport | None
        if isinstance(usage_gap_or_path, (str, Path)):
            usage_gaps = read_model(usage_gap_or_path, UsageGapReport)
        else:
            usage_gaps = usage_gap_or_path
        return build_review_queue(
            packet,
            usage_gaps=usage_gaps,
            include_lower_status=include_lower_status,
            include_watch_usage_gaps=include_watch_usage_gaps,
        )

    def review_dossiers(
        self, review_queue_or_path: ReviewQueue | str | Path
    ) -> CandidateDossierPacket:
        if isinstance(review_queue_or_path, (str, Path)):
            queue = read_model(review_queue_or_path, ReviewQueue)
        else:
            queue = review_queue_or_path
        return build_candidate_dossier_packet(queue)

    def review_summary(
        self, review_queue_or_path: ReviewQueue | str | Path
    ) -> OwnerReviewSummary:
        if isinstance(review_queue_or_path, (str, Path)):
            queue = read_model(review_queue_or_path, ReviewQueue)
        else:
            queue = review_queue_or_path
        return build_owner_review_summary(queue)

    def review_decision_template(
        self,
        review_queue_or_path: ReviewQueue | str | Path,
        *,
        item_ref: str | None = None,
        beacon_ref: str | None = None,
        decision: ReviewDecisionAction = "defer",
        reviewer: str = "owner-review",
        rationale: str = "",
        cluster_ref: str | None = None,
        next_review_after: str | None = None,
    ) -> OwnerReviewDecision:
        if isinstance(review_queue_or_path, (str, Path)):
            queue = read_model(review_queue_or_path, ReviewQueue)
        else:
            queue = review_queue_or_path
        return build_owner_review_decision_template(
            queue,
            item_ref=item_ref,
            beacon_ref=beacon_ref,
            decision=decision,
            reviewer=reviewer,
            rationale=rationale,
            cluster_ref=cluster_ref,
            next_review_after=next_review_after,
        )

    def review_close(
        self,
        review_queue_or_path: ReviewQueue | str | Path,
        *,
        decision_paths: list[str | Path] | None = None,
        decisions: list[OwnerReviewDecision] | None = None,
    ) -> ReviewDecisionCloseReport:
        if isinstance(review_queue_or_path, (str, Path)):
            queue = read_model(review_queue_or_path, ReviewQueue)
        else:
            queue = review_queue_or_path
        loaded_decisions = list(decisions or [])
        if decision_paths:
            loaded_decisions.extend(load_decisions_from_paths(decision_paths))
        return close_review_decisions(
            workspace_root=str(self.workspace.root),
            queue=queue,
            decisions=loaded_decisions,
        )

    def graph_snapshot(
        self, *, include_manifest_diagnostics: bool = True
    ) -> GraphSnapshot:
        return build_graph_snapshot(
            self.workspace,
            registry=self.registry(),
            include_manifest_diagnostics=include_manifest_diagnostics,
        )

    def graph_delta(
        self, before_path: str | Path, after_path: str | Path
    ) -> GraphDeltaReport:
        before = read_model(before_path, GraphSnapshot)
        after = read_model(after_path, GraphSnapshot)
        return diff_graph_snapshots(before, after)

    def graph_closure(
        self,
        *,
        direct_component_refs: list[str],
        depth_limit: int = 8,
        include_optional: bool = True,
    ) -> GraphClosureReport:
        return build_graph_closure_report(
            self.workspace,
            direct_component_refs=direct_component_refs,
            registry=self.registry(),
            depth_limit=depth_limit,
            include_optional=include_optional,
        )

    def routing_projection(
        self,
        *,
        plan_or_path: PropagationPlan | str | Path | None = None,
        gap_report_or_path: ConnectivityGapReport | str | Path | None = None,
        return_handoff_or_path: ReturnHandoff | str | Path | None = None,
        review_queue_or_path: ReviewQueue | str | Path | None = None,
    ) -> RecurrenceRoutingProjection:
        plan: PropagationPlan | None
        if isinstance(plan_or_path, (str, Path)):
            plan = read_model(plan_or_path, PropagationPlan)
        else:
            plan = plan_or_path
        gap_report: ConnectivityGapReport | None
        if isinstance(gap_report_or_path, (str, Path)):
            gap_report = read_model(gap_report_or_path, ConnectivityGapReport)
        else:
            gap_report = gap_report_or_path
        handoff: ReturnHandoff | None
        if isinstance(return_handoff_or_path, (str, Path)):
            handoff = read_model(return_handoff_or_path, ReturnHandoff)
        else:
            handoff = return_handoff_or_path
        queue: ReviewQueue | None
        if isinstance(review_queue_or_path, (str, Path)):
            queue = read_model(review_queue_or_path, ReviewQueue)
        else:
            queue = review_queue_or_path
        return build_routing_projection(
            self.workspace,
            plan=plan,
            gap_report=gap_report,
            return_handoff=handoff,
            review_queue=queue,
        )

    def stats_projection(
        self,
        *,
        gap_report_or_path: ConnectivityGapReport | str | Path | None = None,
        beacon_or_path: BeaconPacket | str | Path | None = None,
        review_queue_or_path: ReviewQueue | str | Path | None = None,
        review_summary_or_path: OwnerReviewSummary | str | Path | None = None,
        decision_report_or_path: ReviewDecisionCloseReport | str | Path | None = None,
    ) -> RecurrenceStatsProjection:
        gap_report: ConnectivityGapReport | None
        if isinstance(gap_report_or_path, (str, Path)):
            gap_report = read_model(gap_report_or_path, ConnectivityGapReport)
        else:
            gap_report = gap_report_or_path
        beacon: BeaconPacket | None
        if isinstance(beacon_or_path, (str, Path)):
            beacon = read_model(beacon_or_path, BeaconPacket)
        else:
            beacon = beacon_or_path
        queue: ReviewQueue | None
        if isinstance(review_queue_or_path, (str, Path)):
            queue = read_model(review_queue_or_path, ReviewQueue)
        else:
            queue = review_queue_or_path
        summary: OwnerReviewSummary | None
        if isinstance(review_summary_or_path, (str, Path)):
            summary = read_model(review_summary_or_path, OwnerReviewSummary)
        else:
            summary = review_summary_or_path
        decision_report: ReviewDecisionCloseReport | None
        if isinstance(decision_report_or_path, (str, Path)):
            decision_report = read_model(
                decision_report_or_path,
                ReviewDecisionCloseReport,
            )
        else:
            decision_report = decision_report_or_path
        return build_stats_projection(
            self.workspace,
            gap_report=gap_report,
            beacon_packet=beacon,
            review_queue=queue,
            review_summary=summary,
            decision_report=decision_report,
            loaded_components=self._loaded_component_refs(),
        )

    def kag_projection(
        self,
        *,
        plan_or_path: PropagationPlan | str | Path | None = None,
        gap_report_or_path: ConnectivityGapReport | str | Path | None = None,
        return_handoff_or_path: ReturnHandoff | str | Path | None = None,
        beacon_or_path: BeaconPacket | str | Path | None = None,
        review_queue_or_path: ReviewQueue | str | Path | None = None,
    ) -> RecurrenceKagProjection:
        plan: PropagationPlan | None
        if isinstance(plan_or_path, (str, Path)):
            plan = read_model(plan_or_path, PropagationPlan)
        else:
            plan = plan_or_path
        gap_report: ConnectivityGapReport | None
        if isinstance(gap_report_or_path, (str, Path)):
            gap_report = read_model(gap_report_or_path, ConnectivityGapReport)
        else:
            gap_report = gap_report_or_path
        handoff: ReturnHandoff | None
        if isinstance(return_handoff_or_path, (str, Path)):
            handoff = read_model(return_handoff_or_path, ReturnHandoff)
        else:
            handoff = return_handoff_or_path
        beacon: BeaconPacket | None
        if isinstance(beacon_or_path, (str, Path)):
            beacon = read_model(beacon_or_path, BeaconPacket)
        else:
            beacon = beacon_or_path
        queue: ReviewQueue | None
        if isinstance(review_queue_or_path, (str, Path)):
            queue = read_model(review_queue_or_path, ReviewQueue)
        else:
            queue = review_queue_or_path
        return build_kag_projection(
            self.workspace,
            plan=plan,
            gap_report=gap_report,
            return_handoff=handoff,
            beacon_packet=beacon,
            review_queue=queue,
        )

    def downstream_projection_bundle(
        self,
        *,
        plan_or_path: PropagationPlan | str | Path | None = None,
        gap_report_or_path: ConnectivityGapReport | str | Path | None = None,
        return_handoff_or_path: ReturnHandoff | str | Path | None = None,
        beacon_or_path: BeaconPacket | str | Path | None = None,
        review_queue_or_path: ReviewQueue | str | Path | None = None,
        review_summary_or_path: OwnerReviewSummary | str | Path | None = None,
        decision_report_or_path: ReviewDecisionCloseReport | str | Path | None = None,
        include_routing: bool = True,
        include_stats: bool = True,
        include_kag: bool = True,
    ) -> DownstreamProjectionBundle:
        plan: PropagationPlan | None
        if isinstance(plan_or_path, (str, Path)):
            plan = read_model(plan_or_path, PropagationPlan)
        else:
            plan = plan_or_path
        gap_report: ConnectivityGapReport | None
        if isinstance(gap_report_or_path, (str, Path)):
            gap_report = read_model(gap_report_or_path, ConnectivityGapReport)
        else:
            gap_report = gap_report_or_path
        handoff: ReturnHandoff | None
        if isinstance(return_handoff_or_path, (str, Path)):
            handoff = read_model(return_handoff_or_path, ReturnHandoff)
        else:
            handoff = return_handoff_or_path
        beacon: BeaconPacket | None
        if isinstance(beacon_or_path, (str, Path)):
            beacon = read_model(beacon_or_path, BeaconPacket)
        else:
            beacon = beacon_or_path
        queue: ReviewQueue | None
        if isinstance(review_queue_or_path, (str, Path)):
            queue = read_model(review_queue_or_path, ReviewQueue)
        else:
            queue = review_queue_or_path
        summary: OwnerReviewSummary | None
        if isinstance(review_summary_or_path, (str, Path)):
            summary = read_model(review_summary_or_path, OwnerReviewSummary)
        else:
            summary = review_summary_or_path
        decision_report: ReviewDecisionCloseReport | None
        if isinstance(decision_report_or_path, (str, Path)):
            decision_report = read_model(
                decision_report_or_path,
                ReviewDecisionCloseReport,
            )
        else:
            decision_report = decision_report_or_path
        return build_downstream_projection_bundle(
            self.workspace,
            plan=plan,
            gap_report=gap_report,
            return_handoff=handoff,
            beacon_packet=beacon,
            review_queue=queue,
            review_summary=summary,
            decision_report=decision_report,
            loaded_components=self._loaded_component_refs(),
            include_routing=include_routing,
            include_stats=include_stats,
            include_kag=include_kag,
        )

    def projection_guard_report(
        self,
        *,
        routing: RecurrenceRoutingProjection | None = None,
        stats: RecurrenceStatsProjection | None = None,
        kag: RecurrenceKagProjection | None = None,
    ) -> DownstreamProjectionGuardReport:
        return build_projection_guard_report(
            self.workspace,
            routing=routing,
            stats=stats,
            kag=kag,
        )

    def wiring_plan(self) -> WiringPlan:
        return build_wiring_plan(self.workspace)

    def rollout_bundle(
        self,
        *,
        wiring_plan_or_path: WiringPlan | str | Path | None = None,
        review_summary_or_path: OwnerReviewSummary | str | Path | None = None,
        doctor_report_or_path: ConnectivityGapReport | str | Path | None = None,
    ) -> RolloutWindowBundle:
        if wiring_plan_or_path is None:
            wiring_plan = self.wiring_plan()
        elif isinstance(wiring_plan_or_path, (str, Path)):
            wiring_plan = read_model(wiring_plan_or_path, WiringPlan)
        else:
            wiring_plan = wiring_plan_or_path
        review_summary: OwnerReviewSummary | None
        if isinstance(review_summary_or_path, (str, Path)):
            review_summary = read_model(review_summary_or_path, OwnerReviewSummary)
        else:
            review_summary = review_summary_or_path
        doctor_report: ConnectivityGapReport | None
        if isinstance(doctor_report_or_path, (str, Path)):
            doctor_report = read_model(doctor_report_or_path, ConnectivityGapReport)
        else:
            doctor_report = doctor_report_or_path
        return build_rollout_window_bundle(
            self.workspace,
            wiring_plan=wiring_plan,
            review_summary=review_summary,
            doctor_report=doctor_report,
        )
