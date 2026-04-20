from __future__ import annotations

from pathlib import Path

from ..workspace.discovery import Workspace
from .beacons import build_beacon_packet
from .detector import detect_change_signal
from .doctor import build_connectivity_gap_report
from .hook_registry import HookRegistry, load_hook_registry
from .hooks import build_hook_run_report, list_hook_bindings
from .io import read_model
from .ledger import build_candidate_ledger
from .models import (
    BeaconPacket,
    CandidateDossierPacket,
    CandidateLedger,
    ChangeSignal,
    ConnectivityGapReport,
    HookBinding,
    HookEvent,
    HookRunReport,
    ObservationPacket,
    OwnerReviewSummary,
    PropagationPlan,
    ReturnHandoff,
    ReviewQueue,
    RolloutWindowBundle,
    UsageGapReport,
    WiringPlan,
)
from .observations import build_observation_packet
from .planner import build_propagation_plan
from .reentry import build_return_handoff
from .registry import RecurrenceRegistry, load_registry
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
        self, report_or_path: ChangeSignal | str | Path | None = None
    ) -> ConnectivityGapReport:
        report = None
        if isinstance(report_or_path, (str, Path)):
            report = read_model(report_or_path, ChangeSignal)
        elif isinstance(report_or_path, ChangeSignal):
            report = report_or_path
        return build_connectivity_gap_report(
            self.workspace, signal=report, registry=self.registry()
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
        if isinstance(review_summary_or_path, (str, Path)):
            review_summary = read_model(review_summary_or_path, OwnerReviewSummary)
        else:
            review_summary = review_summary_or_path
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
