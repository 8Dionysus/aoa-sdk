from __future__ import annotations

from datetime import datetime, timezone

from ..models import ArtifactEnvelope

class AgentsAPI:
    def __init__(self, workspace) -> None:
        self.workspace = workspace

    def binding_for_phase(self, phase: str) -> dict:
        return {"phase": phase, "status": "stub"}

    def new_artifact(self, *, phase: str, payload: dict) -> ArtifactEnvelope:
        return ArtifactEnvelope(
            artifact_type=f"{phase}_artifact",
            phase=phase,
            produced_at=datetime.now(timezone.utc),
            payload=payload,
        )
