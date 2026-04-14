from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..workspace.discovery import Workspace
from .models import RecurrenceComponent, SurfaceClass


SURFACE_GROUPS: tuple[tuple[SurfaceClass, str], ...] = (
    ("source", "source_inputs"),
    ("generated", "generated_surfaces"),
    ("projected", "projected_surfaces"),
    ("contract", "contract_surfaces"),
    ("docs", "documentation_surfaces"),
    ("test", "test_surfaces"),
    ("receipt", "receipt_surfaces"),
)


@dataclass(slots=True)
class LoadedComponent:
    manifest_path: Path
    component: RecurrenceComponent


class RecurrenceRegistry:
    def __init__(self, workspace: Workspace, loaded: list[LoadedComponent]) -> None:
        self.workspace = workspace
        self.loaded = loaded
        self.by_ref = {item.component.component_ref: item for item in loaded}

    def get(self, component_ref: str) -> LoadedComponent | None:
        return self.by_ref.get(component_ref)

    def iter_components(self) -> Iterable[LoadedComponent]:
        return iter(self.loaded)

    def match_path(self, path: str) -> list[tuple[LoadedComponent, SurfaceClass]]:
        normalized = normalize_path(path)
        matches: list[tuple[LoadedComponent, SurfaceClass]] = []
        for item in self.loaded:
            component = item.component
            for surface_class, attr in SURFACE_GROUPS:
                patterns = getattr(component, attr)
                for pattern in patterns:
                    if pattern_matches(pattern, normalized):
                        matches.append((item, surface_class))
                        break
        return matches


def load_registry(workspace: Workspace) -> RecurrenceRegistry:
    loaded: list[LoadedComponent] = []
    for repo, repo_root in workspace.repo_roots.items():
        manifest_root = repo_root / "manifests" / "recurrence"
        if not manifest_root.is_dir():
            continue
        for path in sorted(manifest_root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            component = RecurrenceComponent.model_validate(payload)
            if component.owner_repo != repo:
                component = component.model_copy(update={"owner_repo": repo})
            loaded.append(LoadedComponent(manifest_path=path, component=component))
    return RecurrenceRegistry(workspace, loaded)


def normalize_path(path: str | Path) -> str:
    raw = str(path).replace("\\", "/")
    raw = raw[2:] if raw.startswith("./") else raw
    return raw.strip("/")


def pattern_matches(pattern: str, path: str) -> bool:
    normalized_pattern = normalize_path(pattern)
    normalized_path = normalize_path(path)
    if not normalized_pattern:
        return False
    if normalized_pattern.endswith("/"):
        prefix = normalized_pattern.rstrip("/")
        return normalized_path == prefix or normalized_path.startswith(prefix + "/")
    if "/" not in normalized_pattern and "/" not in normalized_path:
        return fnmatch.fnmatchcase(normalized_path, normalized_pattern)
    return fnmatch.fnmatchcase(normalized_path, normalized_pattern)
