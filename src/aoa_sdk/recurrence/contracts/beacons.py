from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .base import BeaconKind, BeaconStatus, StrictModel


class BeaconEntry(StrictModel):
    beacon_ref: str
    kind: BeaconKind
    status: BeaconStatus
    component_ref: str
    owner_repo: str
    target_repo: str
    decision_surface: str | None = None
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)
    source_inputs: list[str] = Field(default_factory=list)
    related_signals: list[str] = Field(default_factory=list)
    suppression_flags: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class BeaconPacket(StrictModel):
    schema_version: Literal["aoa_beacon_packet_v1"] = "aoa_beacon_packet_v1"
    packet_ref: str
    workspace_root: str
    signal_ref: str | None = None
    entries: list[BeaconEntry] = Field(default_factory=list)


class CandidateLedgerEntry(StrictModel):
    entry_ref: str
    recorded_at: datetime
    beacon_ref: str
    kind: BeaconKind
    status: BeaconStatus
    component_ref: str
    owner_repo: str
    target_repo: str
    decision_surface: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    source_inputs: list[str] = Field(default_factory=list)
    notes: str = ""


class CandidateLedger(StrictModel):
    schema_version: Literal["aoa_candidate_ledger_v1"] = "aoa_candidate_ledger_v1"
    ledger_ref: str
    workspace_root: str
    signal_ref: str | None = None
    entries: list[CandidateLedgerEntry] = Field(default_factory=list)


class UsageGapItem(StrictModel):
    gap_ref: str
    component_ref: str
    owner_repo: str
    beacon_ref: str
    status: BeaconStatus
    reason: str
    decision_surface: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class UsageGapReport(StrictModel):
    schema_version: Literal["aoa_usage_gap_report_v1"] = "aoa_usage_gap_report_v1"
    report_ref: str
    workspace_root: str
    signal_ref: str | None = None
    items: list[UsageGapItem] = Field(default_factory=list)
