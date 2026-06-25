from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from ..contracts.artifacts import (
    ArtifactAffectedReport,
    ArtifactBundleRegistry,
    ArtifactClassificationReport,
    ArtifactProducerProfilesReport,
    ArtifactRequirementsReport,
    ArtifactTrustCoverageReport,
    ArtifactTrustGateReport,
    ArtifactTrustVerdict,
    ArtifactUpdateLaneStatus,
    ArtifactUpdateMetadataVerification,
)
from ..errors import InvalidSurface
from ..loaders.json_file import load_json
from ..workspace.discovery import Workspace


class ArtifactsAPI:
    def __init__(self, workspace: Workspace | None = None) -> None:
        self.workspace = workspace

    def parse_trust_gate(self, payload: dict[str, Any]) -> ArtifactTrustGateReport:
        return ArtifactTrustGateReport.model_validate(payload)

    def load_trust_gate(self, path: str | Path) -> ArtifactTrustGateReport:
        return self.parse_trust_gate(load_json(path))

    def parse_classification(self, payload: dict[str, Any]) -> ArtifactClassificationReport:
        return ArtifactClassificationReport.model_validate(payload)

    def load_classification(self, path: str | Path) -> ArtifactClassificationReport:
        return self.parse_classification(load_json(path))

    def parse_registry(self, payload: dict[str, Any]) -> ArtifactBundleRegistry:
        return ArtifactBundleRegistry.model_validate(payload)

    def load_registry(self, path: str | Path) -> ArtifactBundleRegistry:
        return self.parse_registry(load_json(path))

    def parse_requirements(self, payload: dict[str, Any]) -> ArtifactRequirementsReport:
        return ArtifactRequirementsReport.model_validate(payload)

    def load_requirements(self, path: str | Path) -> ArtifactRequirementsReport:
        return self.parse_requirements(load_json(path))

    def parse_producer_profiles(self, payload: dict[str, Any]) -> ArtifactProducerProfilesReport:
        return ArtifactProducerProfilesReport.model_validate(payload)

    def load_producer_profiles(self, path: str | Path) -> ArtifactProducerProfilesReport:
        return self.parse_producer_profiles(load_json(path))

    def parse_update_lane(self, payload: dict[str, Any]) -> ArtifactUpdateLaneStatus:
        return ArtifactUpdateLaneStatus.model_validate(payload)

    def load_update_lane(self, path: str | Path) -> ArtifactUpdateLaneStatus:
        return self.parse_update_lane(load_json(path))

    def parse_update_verification(self, payload: dict[str, Any]) -> ArtifactUpdateMetadataVerification:
        return ArtifactUpdateMetadataVerification.model_validate(payload)

    def load_update_verification(self, path: str | Path) -> ArtifactUpdateMetadataVerification:
        return self.parse_update_verification(load_json(path))

    def parse_affected(self, payload: dict[str, Any]) -> ArtifactAffectedReport:
        return ArtifactAffectedReport.model_validate(payload)

    def load_affected(self, path: str | Path) -> ArtifactAffectedReport:
        return self.parse_affected(load_json(path))

    def parse_trust_coverage(self, payload: dict[str, Any]) -> ArtifactTrustCoverageReport:
        return ArtifactTrustCoverageReport.model_validate(payload)

    def load_trust_coverage(self, path: str | Path) -> ArtifactTrustCoverageReport:
        return self.parse_trust_coverage(load_json(path))

    def assert_consumable(
        self,
        report: ArtifactTrustGateReport | dict[str, Any],
        *,
        allowed_verdicts: Iterable[ArtifactTrustVerdict] = ("allow", "warn"),
    ) -> ArtifactTrustGateReport:
        parsed = report if isinstance(report, ArtifactTrustGateReport) else self.parse_trust_gate(report)
        allowed = set(allowed_verdicts)
        if parsed.verdict not in allowed or not parsed.decision.allow:
            reasons = parsed.blockers or parsed.reasons or parsed.decision.blockers
            detail = ", ".join(reasons) if reasons else parsed.verdict
            raise InvalidSurface(f"Artifact trust gate did not allow consumption: {detail}")
        return parsed
