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
        return self.verdict in {"allow", "warn"} and self.decision.allow


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


class ArtifactSourceRefStatus(ArtifactHostSurface):
    required: bool = False
    expected: str | None = None
    matched: bool = False
    matched_ref: str | None = None
    known_refs: list[str] = Field(default_factory=list)

    @property
    def proven(self) -> bool:
        return self.required and self.matched and bool(self.matched_ref)


class ArtifactAffectedRow(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    artifact_class: str
    owner_repo: str
    affected: bool
    verdict: ArtifactAffectedVerdict
    freshness: ArtifactAffectedVerdict
    reasons: list[str] = Field(default_factory=list)
    matches: list[str] = Field(default_factory=list)
    changed_source_repo: str | None = None
    contract_surface_status: str | None = None
    registry: dict[str, Any] = Field(default_factory=dict)
    trust_gate: dict[str, Any] = Field(default_factory=dict)
    source_ref_status: ArtifactSourceRefStatus | None = None
    next_actions: list[str] = Field(default_factory=list)
    claim_limit: str | None = None

    @property
    def source_ref_proven(self) -> bool:
        return bool(self.source_ref_status and self.source_ref_status.proven)


class ArtifactAffectedReport(ArtifactHostSurface):
    schema_: str = Field(alias="schema")
    ok: bool
    policy_ref: str | None = None
    abi_ref: str | None = None
    artifact_class_filter: str | None = None
    changed_paths: list[str] = Field(default_factory=list)
    changed_source_repo: str | None = None
    changed_source_ref: str | None = None
    changed_path_source: dict[str, Any] = Field(default_factory=dict)
    accept_sibling_lag: bool = False
    known_verdicts: list[ArtifactAffectedVerdict] = Field(default_factory=list)
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
