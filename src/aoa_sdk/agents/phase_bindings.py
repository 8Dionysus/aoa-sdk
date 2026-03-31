from __future__ import annotations

from datetime import datetime, timezone

from ..compatibility import load_surface
from ..loaders import extract_records
from ..models import ArtifactEnvelope
from ..models import PhaseBinding

class AgentsAPI:
    def __init__(self, workspace) -> None:
        self.workspace = workspace

    def bindings(self) -> list[PhaseBinding]:
        data = load_surface(self.workspace, "aoa-agents.runtime_seam_bindings")
        records = extract_records(data, preferred_keys=("bindings",))
        return [PhaseBinding.model_validate(item) for item in records]

    def binding_for_phase(self, phase: str) -> PhaseBinding:
        for binding in self.bindings():
            if binding.phase == phase:
                return binding
        raise ValueError(f"Unknown phase: {phase}")

    def artifact_type_for_phase(self, phase: str) -> str:
        return self.binding_for_phase(phase).artifact_type

    def roles_for_phase(self, phase: str) -> list[str]:
        return self.binding_for_phase(phase).role_names

    def new_artifact(self, *, phase: str, payload: dict) -> ArtifactEnvelope:
        binding = self.binding_for_phase(phase)
        return ArtifactEnvelope(
            artifact_type=binding.artifact_type,
            phase=phase,
            produced_at=datetime.now(timezone.utc),
            payload=payload,
        )
