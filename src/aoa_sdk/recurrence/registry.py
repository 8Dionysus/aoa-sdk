from __future__ import annotations

import fnmatch
import shlex
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..workspace.discovery import Workspace
from .compat import classify_manifest, validate_recurrence_component_payload
from .models import (
    ManifestDiagnostic,
    ManifestKind,
    ManifestScanReport,
    RecurrenceComponent,
    SurfaceClass,
)


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


@dataclass(slots=True)
class LoadedForeignManifest:
    manifest_path: Path
    repo: str
    manifest_kind: ManifestKind
    manifest_ref: str


class RecurrenceRegistry:
    def __init__(
        self,
        workspace: Workspace,
        loaded: list[LoadedComponent],
        *,
        foreign_manifests: list[LoadedForeignManifest] | None = None,
        diagnostics: list[ManifestDiagnostic] | None = None,
    ) -> None:
        self.workspace = workspace
        self.loaded = loaded
        self.foreign_manifests = foreign_manifests or []
        self.diagnostics = diagnostics or []
        self.by_ref = {item.component.component_ref: item for item in loaded}

    def get(self, component_ref: str) -> LoadedComponent | None:
        return self.by_ref.get(component_ref)

    def iter_components(self) -> Iterable[LoadedComponent]:
        return iter(self.loaded)

    def iter_foreign_manifests(self) -> Iterable[LoadedForeignManifest]:
        return iter(self.foreign_manifests)

    def iter_manifest_diagnostics(self) -> Iterable[ManifestDiagnostic]:
        return iter(self.diagnostics)

    def match_path(
        self, path: str | Path, *, owner_repo: str | None = None
    ) -> list[tuple[LoadedComponent, SurfaceClass]]:
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

    def manifest_scan_report(self) -> ManifestScanReport:
        return build_manifest_scan_report(self.workspace, registry=self)


def load_registry(workspace: Workspace) -> RecurrenceRegistry:
    loaded: list[LoadedComponent] = []
    foreign_manifests: list[LoadedForeignManifest] = []
    diagnostics: list[ManifestDiagnostic] = []
    for repo, repo_root in workspace.repo_roots.items():
        manifest_root = repo_root / "manifests" / "recurrence"
        if not manifest_root.is_dir():
            continue
        for path in sorted(manifest_root.rglob("*.json")):
            classification = classify_manifest(repo, repo_root, path)
            diagnostics.extend(classification.diagnostics)

            if classification.payload is None:
                continue

            if classification.manifest_kind != "recurrence_component":
                foreign_manifests.append(
                    LoadedForeignManifest(
                        manifest_path=path,
                        repo=repo,
                        manifest_kind=classification.manifest_kind,
                        manifest_ref=classification.manifest_ref,
                    )
                )
                continue

            component, component_diagnostics = validate_recurrence_component_payload(
                repo=repo,
                repo_root=repo_root,
                path=path,
                payload=classification.payload,
            )
            diagnostics.extend(component_diagnostics)
            if component is None:
                if any(
                    diagnostic.manifest_kind == "agon_recurrence_adapter"
                    for diagnostic in component_diagnostics
                ):
                    foreign_manifests.append(
                        LoadedForeignManifest(
                            manifest_path=path,
                            repo=repo,
                            manifest_kind="agon_recurrence_adapter",
                            manifest_ref=classification.manifest_ref,
                        )
                    )
                continue

            loaded.append(LoadedComponent(manifest_path=path, component=component))
    return RecurrenceRegistry(
        workspace,
        loaded,
        foreign_manifests=foreign_manifests,
        diagnostics=diagnostics,
    )


def build_manifest_scan_report(
    workspace: Workspace,
    *,
    registry: RecurrenceRegistry | None = None,
) -> ManifestScanReport:
    registry = registry or load_registry(workspace)
    by_kind = Counter(item.manifest_kind for item in registry.iter_foreign_manifests())
    by_kind.update({"recurrence_component": len(list(registry.iter_components()))})
    by_severity = Counter(item.severity for item in registry.iter_manifest_diagnostics())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ManifestScanReport(
        report_ref=f"manifest-scan:{stamp}",
        workspace_root=str(workspace.federation_root),
        loaded_components=sorted(
            item.component.component_ref for item in registry.iter_components()
        ),
        foreign_manifests=sorted(
            item.manifest_ref for item in registry.iter_foreign_manifests()
        ),
        diagnostics=list(registry.iter_manifest_diagnostics()),
        by_kind=dict(sorted(by_kind.items())),
        by_severity=dict(sorted(by_severity.items())),
    )


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


def pattern_matches(pattern: str, path: str | Path) -> bool:
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
