from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_CONFIG_ENV = "AOA_SDK_WORKSPACE_CONFIG"
FEDERATION_ROOT_ENV = "AOA_SDK_FEDERATION_ROOT"
EXTERNAL_ROOTS_ENV = "AOA_SDK_EXTERNAL_ROOTS"
ORGAN_REGISTRY_ENV = "AOA_SDK_ORGAN_REGISTRY"
ROUTING_BUNDLE_ROOT_ENV = "AOA_SDK_ROUTING_BUNDLE_ROOT"
ROUTING_SOURCE_LOCK_ENV = "AOA_SDK_ROUTING_SOURCE_LOCK"
REPO_PATH_ENV_PREFIX = "AOA_SDK_REPO_PATH_"
DEFAULT_WORKSPACE_MANIFEST = ".aoa/workspace.toml"
SUPPORTED_SCHEMA_VERSION = 1


@dataclass(slots=True)
class RepoConfig:
    role: str | None = None
    preferred: tuple[str, ...] = ()
    runtime_mirror: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class WorkspaceConfig:
    start: Path
    manifest_path: Path | None
    federation_root_patterns: tuple[str, ...] = ()
    external_root_patterns: tuple[str, ...] = ()
    repo_configs: dict[str, RepoConfig] = field(default_factory=dict)
    organ_registry_pattern: str | None = None
    routing_bundle_root_pattern: str | None = None
    routing_source_lock_pattern: str | None = None


def load_workspace_config(root: str | Path) -> WorkspaceConfig:
    resolved = Path(root).expanduser().resolve()
    start = resolved if resolved.is_dir() else resolved.parent
    manifest_path = find_workspace_manifest(start)
    manifest = _load_manifest(manifest_path) if manifest_path is not None else {}

    layout = manifest.get("layout", {})
    roots = manifest.get("roots", {})
    repos = manifest.get("repos", {})
    organ_access = manifest.get("organ_access", {})
    control_plane = manifest.get("control_plane", {})

    repo_configs = {
        repo: RepoConfig(
            role=spec.get("role"),
            preferred=_as_tuple(spec.get("preferred")),
            runtime_mirror=spec.get("runtime_mirror"),
            notes=spec.get("notes"),
        )
        for repo, spec in repos.items()
        if isinstance(spec, dict)
    }

    return WorkspaceConfig(
        start=start,
        manifest_path=manifest_path,
        federation_root_patterns=_as_tuple(layout.get("federation_roots")),
        external_root_patterns=_as_tuple(roots.get("external")),
        repo_configs=repo_configs,
        organ_registry_pattern=(
            organ_access.get("registry_source")
            if isinstance(organ_access, dict)
            and isinstance(organ_access.get("registry_source"), str)
            else None
        ),
        routing_bundle_root_pattern=(
            control_plane.get("routing_bundle_root")
            if isinstance(control_plane, dict)
            and isinstance(control_plane.get("routing_bundle_root"), str)
            else None
        ),
        routing_source_lock_pattern=(
            control_plane.get("routing_source_lock")
            if isinstance(control_plane, dict)
            and isinstance(control_plane.get("routing_source_lock"), str)
            else None
        ),
    )


def find_workspace_manifest(start: Path) -> Path | None:
    env_path = os.environ.get(WORKSPACE_CONFIG_ENV)
    if env_path:
        return Path(env_path).expanduser().resolve(strict=False)

    for candidate_root in (start, *start.parents):
        candidate = candidate_root / DEFAULT_WORKSPACE_MANIFEST
        if candidate.is_file():
            return candidate.resolve()
    return None


def resolve_pattern(pattern: str, config: WorkspaceConfig) -> Path:
    workspace_root = _pattern_workspace_root(config)
    rendered = pattern.format(
        workspace_root=str(workspace_root),
        workspace_parent=str(workspace_root.parent),
        home=str(Path.home()),
    )
    path = Path(rendered).expanduser()
    if not path.is_absolute() and config.manifest_path is not None:
        path = config.manifest_path.parent / path
    return path.resolve(strict=False)


def _pattern_workspace_root(config: WorkspaceConfig) -> Path:
    manifest_path = config.manifest_path
    if manifest_path is not None and manifest_path.parent.name == ".aoa":
        return manifest_path.parent.parent
    return config.start


def repo_env_var_name(repo: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in repo).upper()
    return f"{REPO_PATH_ENV_PREFIX}{normalized}"


def _load_manifest(path: Path) -> dict:
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    schema_version = data.get("schema_version", SUPPORTED_SCHEMA_VERSION)
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported workspace manifest schema version {schema_version!r}; "
            f"expected {SUPPORTED_SCHEMA_VERSION}"
        )
    return data


def _as_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, str))
    return ()
