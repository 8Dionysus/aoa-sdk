from __future__ import annotations

import fnmatch
import json
import shlex
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
    ("proof", "proof_surfaces"),
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

    def match_path(self, path: str, *, owner_repo: str | None = None) -> list[tuple[LoadedComponent, SurfaceClass]]:
        normalized = normalize_path(path)
        matches: list[tuple[LoadedComponent, SurfaceClass]] = []
        for item in self.loaded:
            component = item.component
            if owner_repo is not None and component.owner_repo != owner_repo:
                continue
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


def normalize_path(path: str | Path, *, preserve_trailing_slash: bool = False) -> str:
    raw = str(path).replace("\\", "/")
    raw = raw[2:] if raw.startswith("./") else raw
    had_trailing_slash = raw.endswith("/")
    normalized = raw.strip("/")
    if preserve_trailing_slash and had_trailing_slash and normalized:
        return normalized + "/"
    return normalized


def _looks_like_path_pattern(pattern: str) -> bool:
    if any(token in pattern for token in ("*", "?", "[")):
        return True
    if "/" in pattern:
        return True
    name = Path(pattern.rstrip("/")).name
    return "." in name or pattern.startswith(".")


def _iter_match_patterns(pattern: str) -> Iterable[str]:
    normalized = normalize_path(pattern, preserve_trailing_slash=True)
    if normalized:
        yield normalized

    try:
        tokens = shlex.split(str(pattern))
    except ValueError:
        tokens = str(pattern).split()

    for token in tokens:
        if token.startswith("-"):
            continue
        candidate = normalize_path(token, preserve_trailing_slash=True)
        if not candidate or candidate == normalized or not _looks_like_path_pattern(candidate):
            continue
        yield candidate


def pattern_matches(pattern: str, path: str) -> bool:
    normalized_path = normalize_path(path)
    for normalized_pattern in _iter_match_patterns(pattern):
        if normalized_pattern.endswith("/"):
            prefix = normalized_pattern.rstrip("/")
            if normalized_path == prefix or normalized_path.startswith(prefix + "/"):
                return True
            continue
        if "/" not in normalized_pattern and "/" not in normalized_path:
            if fnmatch.fnmatchcase(normalized_path, normalized_pattern):
                return True
            continue
        if fnmatch.fnmatchcase(normalized_path, normalized_pattern):
            return True
    return False
