from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from ..workspace.discovery import Workspace
from .models import (
    BeaconPacket,
    CandidateDossierPacket,
    CandidateLedger,
    ChangeSignal,
    ConnectivityGapReport,
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

ModelT = TypeVar("ModelT", bound=BaseModel)


def control_plane_root(workspace: Workspace) -> Path:
    sdk_root = workspace.repo_roots.get("aoa-sdk")
    base = sdk_root if sdk_root is not None else workspace.root
    return base / ".aoa" / "recurrence"


def _default_path(workspace: Workspace, family: str, label: str) -> Path:
    safe_label = label.replace("/", ".").replace(":", ".")
    return control_plane_root(workspace) / family / f"{safe_label}.latest.json"


def write_model(path: str | Path, model: BaseModel) -> Path:
    resolved = Path(path).expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(model.model_dump(mode="json"), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return resolved


def read_model(path: str | Path, model_type: type[ModelT]) -> ModelT:
    payload = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    return model_type.model_validate(payload)


def persist_change_signal(
    workspace: Workspace, signal: ChangeSignal, output: str | None = None
) -> Path:
    label = signal.repo_name or Path(signal.repo_root).name
    path = output or str(_default_path(workspace, "signals", label))
    return write_model(path, signal)


def persist_propagation_plan(
    workspace: Workspace, plan: PropagationPlan, output: str | None = None
) -> Path:
    label = plan.direct_components[0] if plan.direct_components else "workspace"
    path = output or str(_default_path(workspace, "plans", label))
    return write_model(path, plan)


def persist_gap_report(
    workspace: Workspace, report: ConnectivityGapReport, output: str | None = None
) -> Path:
    label = report.signal_ref or "workspace"
    path = output or str(_default_path(workspace, "doctor", label))
    return write_model(path, report)


def persist_return_handoff(
    workspace: Workspace, handoff: ReturnHandoff, output: str | None = None
) -> Path:
    path = output or str(_default_path(workspace, "handoffs", handoff.plan_ref))
    return write_model(path, handoff)


def persist_hook_run_report(
    workspace: Workspace,
    report: HookRunReport,
    output: str | None = None,
) -> Path:
    label = report.signal_ref or report.event
    path = output or str(_default_path(workspace, "hooks", label))
    return write_model(path, report)


def persist_observation_packet(
    workspace: Workspace,
    packet: ObservationPacket,
    output: str | None = None,
) -> Path:
    label = packet.signal_ref or "workspace"
    path = output or str(_default_path(workspace, "observations", label))
    return write_model(path, packet)


def persist_beacon_packet(
    workspace: Workspace, packet: BeaconPacket, output: str | None = None
) -> Path:
    label = packet.signal_ref or packet.packet_ref
    path = output or str(_default_path(workspace, "beacons", label))
    return write_model(path, packet)


def persist_candidate_ledger(
    workspace: Workspace,
    ledger: CandidateLedger,
    output: str | None = None,
) -> Path:
    label = ledger.signal_ref or ledger.ledger_ref
    path = output or str(_default_path(workspace, "ledger", label))
    return write_model(path, ledger)


def persist_usage_gap_report(
    workspace: Workspace,
    report: UsageGapReport,
    output: str | None = None,
) -> Path:
    label = report.signal_ref or report.report_ref
    path = output or str(_default_path(workspace, "usage-gaps", label))
    return write_model(path, report)


def persist_review_queue(
    workspace: Workspace,
    queue: ReviewQueue,
    output: str | None = None,
) -> Path:
    label = queue.signal_ref or queue.queue_ref
    path = output or str(_default_path(workspace, "review-queues", label))
    return write_model(path, queue)


def persist_candidate_dossier_packet(
    workspace: Workspace,
    packet: CandidateDossierPacket,
    output: str | None = None,
) -> Path:
    label = packet.signal_ref or packet.packet_ref
    path = output or str(_default_path(workspace, "review-dossiers", label))
    return write_model(path, packet)


def persist_owner_review_summary(
    workspace: Workspace,
    summary: OwnerReviewSummary,
    output: str | None = None,
) -> Path:
    label = summary.signal_ref or summary.summary_ref
    path = output or str(_default_path(workspace, "review-summaries", label))
    return write_model(path, summary)


def persist_wiring_plan(
    workspace: Workspace,
    plan: WiringPlan,
    output: str | None = None,
) -> Path:
    label = plan.plan_ref
    path = output or str(_default_path(workspace, "wiring-plans", label))
    return write_model(path, plan)


def persist_rollout_window_bundle(
    workspace: Workspace,
    bundle: RolloutWindowBundle,
    output: str | None = None,
) -> Path:
    label = bundle.bundle_ref
    path = output or str(_default_path(workspace, "rollout-bundles", label))
    return write_model(path, bundle)
