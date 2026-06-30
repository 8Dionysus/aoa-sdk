from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ArtifactTrustVerdict = Literal["allow", "warn", "deny", "unknown", "manual_review_required"]
ArtifactAffectedVerdict = Literal[
    "fresh",
    "stale",
    "needs_rebuild",
    "needs_reverify",
    "blocked_by_missing_sibling",
    "accepted_lag",
    "manual_review_required",
]
ArtifactDriftStatus = Literal[
    "fresh",
    "missing_durable_evidence",
    "rebuild_required",
    "reverify_required",
    "blocked_missing_sibling",
    "accepted_lag",
    "manual_review_required",
]


class ArtifactHostSurface(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ArtifactTrustDecision(ArtifactHostSurface):
    allow: bool
    verdict: ArtifactTrustVerdict
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    manual_review: list[str] = Field(default_factory=list)
    consumer_intent: str | None = None
    model: str | None = None


class ArtifactTrustGateReport(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    artifact_class: str
    consumer_intent: str
    verdict: ArtifactTrustVerdict
    decision: ArtifactTrustDecision
    record_id: str | None = None
    subject_digest: str | None = None
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    inspected_claims: dict[str, Any] = Field(default_factory=dict)

    @property
    def consumable(self) -> bool:
        return self.ok and self.verdict in {"allow", "warn"} and self.decision.allow


class ArtifactClassificationReport(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    artifact_class: str
    bundle_layout: str | None = None
    target: str | None = None
    policy_ref: str | None = None
    policy_version: str | None = None
    identity: dict[str, Any] = Field(default_factory=dict)
    required_controls: list[str] = Field(default_factory=list)
    deferred_controls: dict[str, Any] = Field(default_factory=dict)
    required_sidecars: dict[str, list[str]] = Field(default_factory=dict)
    signature_required: bool | None = None


class ArtifactBundleRegistryRecord(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    record_id: str
    artifact_class: str
    subject_digest: str
    source_repo: str
    source_ref: str
    source_refs: list[str] = Field(default_factory=list)
    bundle_manifest_ref: str | None = None
    producer: str
    producer_command: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    trust_root_mode: str
    lifecycle_state: str
    latest_eligible: bool
    terminal_state: bool
    verifier_versions: dict[str, Any] = Field(default_factory=dict)
    controls: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None
    supersedes: str | None = None
    superseded_by: str | None = None
    revoked_at: str | None = None
    revoked_by: str | None = None
    revocation_reason: str | None = None


class ArtifactBundleRegistry(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    records: list[ArtifactBundleRegistryRecord] = Field(default_factory=list)
    latest_by_artifact_class: dict[str, ArtifactBundleRegistryRecord] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)


class ArtifactRequirementRow(ArtifactHostSurface):
    schema_: str | None = Field(default=None, alias="schema")
    artifact_class: str
    owner_repo: str
    controls: dict[str, Any] = Field(default_factory=dict)
    producer_profile: dict[str, Any] = Field(default_factory=dict)
    source_route: dict[str, Any] = Field(default_factory=dict)
    trust_roots: dict[str, Any] = Field(default_factory=dict)
    registry_status: dict[str, Any] = Field(default_factory=dict)
    trust_gate_status: dict[str, Any] = Field(default_factory=dict)
    consumer: dict[str, Any] = Field(default_factory=dict)
    release_rules: dict[str, Any] = Field(default_factory=dict)
    agent_loop: dict[str, str] = Field(default_factory=dict)
    claim_limits: list[str] = Field(default_factory=list)


class ArtifactRequirementsReport(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    rows: list[ArtifactRequirementRow] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class ArtifactProducerProfile(ArtifactHostSurface):
    profile_id: str
    owner_repo: str
    owner_route_refs: list[str] = Field(default_factory=list)
    artifact_classes: list[str] = Field(default_factory=list)
    release_export_triggers: list[str] = Field(default_factory=list)
    validator_commands: list[str] = Field(default_factory=list)
    produced_sidecars: list[str] = Field(default_factory=list)
    consumer_expectations: list[str] = Field(default_factory=list)
    owner_boundaries: list[str] = Field(default_factory=list)
    trust_root_modes: list[str] = Field(default_factory=list)


class ArtifactProducerProfilesReport(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    policy_ref: str | None = None
    policy_version: str | None = None
    abi_ref: str | None = None
    profile_filter: str | None = None
    owner_repo_filter: str | None = None
    artifact_class_filter: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    rows: list[ArtifactProducerProfile] = Field(default_factory=list)
    agent_loop: dict[str, str] = Field(default_factory=dict)
    claim_limits: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    latest: str | None = None

    @property
    def read_model_only(self) -> bool:
        return True

    def for_artifact_class(self, artifact_class: str) -> list[ArtifactProducerProfile]:
        return [row for row in self.rows if artifact_class in row.artifact_classes]

    def for_owner_repo(self, owner_repo: str) -> list[ArtifactProducerProfile]:
        return [row for row in self.rows if row.owner_repo == owner_repo]


class ArtifactUpdateLaneRow(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    artifact_class: str
    applies: bool
    consumer_intent: str
    metadata_sidecar: str
    required_when: str | None = None
    client_checks: list[str] = Field(default_factory=list)
    status: str


class ArtifactUpdateLaneStatus(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    rows: list[ArtifactUpdateLaneRow] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    tuf: dict[str, Any] = Field(default_factory=dict)
    scitt: dict[str, Any] = Field(default_factory=dict)
    claim_limits: list[str] = Field(default_factory=list)

    @property
    def tuf_status(self) -> str | None:
        value = self.summary.get("tuf_status")
        return str(value) if value else None

    @property
    def scitt_status(self) -> str | None:
        value = self.summary.get("scitt_status")
        return str(value) if value else None

    @property
    def has_structural_tuf_repository_verifier(self) -> bool:
        verifier = self.tuf.get("external_repository_verifier")
        return isinstance(verifier, dict) and verifier.get("status") == "structural_v1"

    @property
    def has_scitt_receipt_binding_stub(self) -> bool:
        return self.scitt_status == "local_stub_fail_closed_external_v1"

    @property
    def external_relying_party_receipt_required(self) -> bool:
        mode = self.scitt.get("external_relying_party_mode")
        return isinstance(mode, dict) and mode.get("receipt_required") is True


class ArtifactUpdateMetadataVerification(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    verdict: ArtifactTrustVerdict
    artifact_class: str | None = None
    metadata_sha256: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checked: dict[str, Any] = Field(default_factory=dict)

    @property
    def update_consideration_allowed(self) -> bool:
        return self.ok and self.verdict == "allow"


class ArtifactScittReceiptVerification(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    verdict: ArtifactTrustVerdict
    policy_ref: str | None = None
    statement_schema: str | None = None
    receipt_schema: str | None = None
    statement_digest: str | None = None
    statement_class: str | None = None
    issuer: str | None = None
    artifact_digest: str | None = None
    external_relying_party: bool = False
    receipt_required: bool = False
    receipt_present: bool = False
    receipt_ok: bool = False
    transparency_service: str | None = None
    known_statement_classes: list[str] = Field(default_factory=list)
    scitt_policy: dict[str, Any] = Field(default_factory=dict)
    checked: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    claim_limits: list[str] = Field(default_factory=list)
    statement_path: str | None = None
    receipt_path: str | None = None

    @property
    def consumable(self) -> bool:
        return self.ok and self.verdict == "allow"

    @property
    def external_relying_party_allowed(self) -> bool:
        return (
            self.consumable
            and self.external_relying_party
            and self.receipt_required
            and self.receipt_present
            and self.receipt_ok
        )

    @property
    def fail_closed_missing_receipt(self) -> bool:
        return (
            self.external_relying_party
            and self.receipt_required
            and not self.receipt_present
            and self.verdict == "deny"
            and "scitt_receipt_required" in self.errors
        )


class ArtifactSourceRefStatus(ArtifactHostSurface):
    required: bool = False
    expected: str | None = None
    matched: bool | None = None
    matched_ref: str | None = None
    known_refs: list[str] = Field(default_factory=list)

    @property
    def proven(self) -> bool:
        return self.required and self.matched is True and bool(self.matched_ref)


class ArtifactDriftState(ArtifactHostSurface):
    status: ArtifactDriftStatus
    known_statuses: list[ArtifactDriftStatus] = Field(default_factory=list)
    operationally_blocking: bool = False
    needs_rebuild: bool = False
    needs_reverify: bool = False
    accepted_lag: bool = False
    lag_policy: str | None = None
    source_ref_state: str | None = None
    evidence_state: str | None = None
    reason_count: int = 0
    explanation: str | None = None

    @property
    def blocks_operation(self) -> bool:
        return self.operationally_blocking

    @property
    def current_proof_missing(self) -> bool:
        return self.source_ref_state == "missing_current_proof"


class ArtifactChangedPathAnalysis(ArtifactHostSurface):
    raw: str
    normalized: str
    source_repo: str | None = None
    source_repo_inferred: bool = False
    scope: str | None = None


class ArtifactAffectedRow(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    artifact_class: str
    owner_repo: str
    affected: bool
    verdict: ArtifactAffectedVerdict
    freshness: ArtifactAffectedVerdict
    reasons: list[str] = Field(default_factory=list)
    matches: list[str | dict[str, Any]] = Field(default_factory=list)
    changed_source_repo: str | None = None
    changed_source_repo_inferred: str | None = None
    contract_surface_status: str | None = None
    drift: ArtifactDriftState | None = None
    registry: dict[str, Any] = Field(default_factory=dict)
    trust_gate: dict[str, Any] = Field(default_factory=dict)
    source_ref_status: ArtifactSourceRefStatus | None = None
    next_actions: list[str] = Field(default_factory=list)
    claim_limit: str | None = None

    @property
    def source_ref_proven(self) -> bool:
        return bool(self.source_ref_status and self.source_ref_status.proven)

    @property
    def operationally_blocking(self) -> bool:
        return bool(self.drift and self.drift.operationally_blocking)

    @property
    def lag_accepted(self) -> bool:
        return bool(self.drift and self.drift.accepted_lag)


class ArtifactAffectedReport(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    policy_ref: str | None = None
    abi_ref: str | None = None
    artifact_class_filter: str | None = None
    changed_paths: list[str] = Field(default_factory=list)
    raw_changed_paths: list[str] = Field(default_factory=list)
    changed_path_analysis: list[ArtifactChangedPathAnalysis] = Field(default_factory=list)
    changed_source_repo: str | None = None
    changed_source_repo_inferred: str | None = None
    changed_source_ref: str | None = None
    changed_path_source: dict[str, Any] | str | None = Field(default_factory=dict)
    accept_sibling_lag: bool = False
    known_verdicts: list[ArtifactAffectedVerdict] = Field(default_factory=list)
    known_drift_statuses: list[ArtifactDriftStatus] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    rows: list[ArtifactAffectedRow] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    latest: str | None = None


class ArtifactTrustCoverageRow(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    artifact_class: str
    owner: str
    real_artifact: dict[str, Any] = Field(default_factory=dict)
    required_controls: list[str] = Field(default_factory=list)
    deferred_controls: dict[str, Any] = Field(default_factory=dict)
    source_verification: list[str] = Field(default_factory=list)
    installed_verification: dict[str, Any] = Field(default_factory=dict)
    persistent_registry_status: dict[str, Any] = Field(default_factory=dict)
    consumer_path: dict[str, Any] = Field(default_factory=dict)
    manual_positive_evidence: list[str] = Field(default_factory=list)
    manual_negative_evidence: list[str] = Field(default_factory=list)
    external_signature_provenance_status: str | None = None
    claim_limits: list[str] = Field(default_factory=list)
    status: str
    remaining_blocker: str = ""


class ArtifactTrustCoverageReport(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    summary: dict[str, Any] = Field(default_factory=dict)
    policy_ref: str | None = None
    abi_ref: str | None = None
    registry: dict[str, Any] = Field(default_factory=dict)
    trust_tools: dict[str, Any] = Field(default_factory=dict)
    manual_evidence_roots: list[str] = Field(default_factory=list)
    rows: list[ArtifactTrustCoverageRow] = Field(default_factory=list)
    latest: str | None = None
    claim_limits: list[str] = Field(default_factory=list)
