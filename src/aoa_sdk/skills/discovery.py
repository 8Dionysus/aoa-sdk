from __future__ import annotations

class SkillsAPI:
    def __init__(self, workspace) -> None:
        self.workspace = workspace

    def discover(self, **kwargs) -> dict:
        return {"operation": "discover", "kwargs": kwargs, "status": "stub"}

    def disclose(self, skill_name: str) -> dict:
        return {"operation": "disclose", "skill_name": skill_name, "status": "stub"}

    def activate(self, skill_name: str, **kwargs) -> dict:
        return {"operation": "activate", "skill_name": skill_name, "kwargs": kwargs, "status": "stub"}
