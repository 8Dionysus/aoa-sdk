from __future__ import annotations

from pathlib import Path

from ..errors import RecordNotFound
from ..loaders.json_file import load_json
from ..models import (
    GovernedRunReviewHandoffBundle,
    GovernedRunReviewPacketAudit,
    GovernedRunReviewPacketManifest,
)
from ..workspace.discovery import Workspace


class GovernedRunsAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def manifest(self, run_dir: str | Path) -> GovernedRunReviewPacketManifest:
        data = load_json(self._artifact_path(run_dir, "review_packet_manifest.json"))
        return GovernedRunReviewPacketManifest.model_validate(data)

    def audit(self, run_dir: str | Path) -> GovernedRunReviewPacketAudit:
        data = load_json(self._artifact_path(run_dir, "review_packet_audit.json"))
        return GovernedRunReviewPacketAudit.model_validate(data)

    def handoff_bundle(self, run_dir: str | Path) -> GovernedRunReviewHandoffBundle:
        data = load_json(self._artifact_path(run_dir, "review_handoff_bundle.json"))
        return GovernedRunReviewHandoffBundle.model_validate(data)

    def _artifact_path(self, run_dir: str | Path, filename: str) -> Path:
        resolved_run_dir = self._resolve_run_dir(run_dir)
        artifact_path = resolved_run_dir / "artifacts" / filename
        if not artifact_path.is_file():
            raise RecordNotFound(f"Missing governed run artifact: {artifact_path}")
        return artifact_path

    def _resolve_run_dir(self, run_dir: str | Path) -> Path:
        candidate = Path(run_dir).expanduser()
        if candidate.is_absolute():
            resolved = candidate.resolve(strict=False)
            if resolved.is_dir():
                return resolved
        else:
            stack_root = self.workspace.repo_path("abyss-stack")
            direct_candidate = (stack_root / candidate).resolve(strict=False)
            if direct_candidate.is_dir():
                return direct_candidate
            governed_candidate = (stack_root / "Logs" / "governed-runs" / candidate).resolve(strict=False)
            if governed_candidate.is_dir():
                return governed_candidate
        raise RecordNotFound(f"Unknown governed run directory: {run_dir}")
