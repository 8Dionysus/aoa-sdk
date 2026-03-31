from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..errors import RepoNotFound
from .config import (
    EXTERNAL_ROOTS_ENV,
    FEDERATION_ROOT_ENV,
    WorkspaceConfig,
    load_workspace_config,
    repo_env_var_name,
    resolve_pattern,
)
from .roots import (
    DEFAULT_EXTERNAL_ROOT_PATTERNS,
    DEFAULT_PREFERRED_REPO_PATH_PATTERNS,
    KNOWN_REPOS,
    REPO_MARKERS,
)


@dataclass(slots=True)
class Workspace:
    root: Path
    federation_root: Path
    federation_root_source: str
    manifest_path: Path | None
    repo_roots: dict[str, Path]
    repo_origins: dict[str, str]

    @classmethod
    def discover(cls, root: str | Path) -> "Workspace":
        resolved = Path(root).expanduser().resolve()
        start = resolved if resolved.is_dir() else resolved.parent

        config = load_workspace_config(start)
        federation_root, federation_root_source = _discover_federation_root(start=start, config=config)

        repo_roots = {}
        repo_origins = {}
        for repo in KNOWN_REPOS:
            resolved_repo = _discover_repo_path(repo=repo, federation_root=federation_root, config=config)
            if resolved_repo is not None:
                path, origin = resolved_repo
                repo_roots[repo] = path
                repo_origins[repo] = origin
        return cls(
            root=start,
            federation_root=federation_root,
            federation_root_source=federation_root_source,
            manifest_path=config.manifest_path,
            repo_roots=repo_roots,
            repo_origins=repo_origins,
        )

    def has_repo(self, repo: str) -> bool:
        return repo in self.repo_roots

    def repo_path(self, repo: str) -> Path:
        path = self.repo_roots.get(repo)
        if path is None:
            raise RepoNotFound(f"Repository {repo!r} is not available under {self.federation_root}")
        return path

    def surface_path(self, repo: str, relative_path: str | Path) -> Path:
        return self.repo_path(repo) / Path(relative_path)


def _discover_federation_root(*, start: Path, config: WorkspaceConfig) -> tuple[Path, str]:
    env_root = os.environ.get(FEDERATION_ROOT_ENV)
    if env_root:
        candidate = Path(env_root).expanduser().resolve(strict=False)
        if candidate.is_dir():
            return candidate, f"env:{FEDERATION_ROOT_ENV}"

    for pattern in config.federation_root_patterns:
        candidate = resolve_pattern(pattern, config)
        if candidate.is_dir():
            return candidate, "manifest:layout.federation_roots"

    for candidate in (start, *start.parents):
        repo_roots = {
            repo: candidate / repo
            for repo in KNOWN_REPOS
            if _is_repo_root(candidate / repo)
        }
        if len(repo_roots) >= 2:
            return candidate, "auto:ancestor-scan"

    return start, "auto:start"


def _discover_repo_path(
    *,
    repo: str,
    federation_root: Path,
    config: WorkspaceConfig,
) -> tuple[Path, str] | None:
    for candidate, origin in _repo_candidates(repo=repo, federation_root=federation_root, config=config):
        if _is_repo_root(candidate):
            return candidate, origin
    return None


def _repo_candidates(
    *,
    repo: str,
    federation_root: Path,
    config: WorkspaceConfig,
) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []

    env_var = repo_env_var_name(repo)
    env_path = os.environ.get(env_var)
    if env_path:
        candidates.append((Path(env_path).expanduser().resolve(strict=False), f"env:{env_var}"))

    repo_config = config.repo_configs.get(repo)
    if repo_config is not None:
        for pattern in repo_config.preferred:
            candidates.append((resolve_pattern(pattern, config), f"manifest:repos.{repo}.preferred"))

    for pattern in DEFAULT_PREFERRED_REPO_PATH_PATTERNS.get(repo, ()):
        candidates.append((Path(pattern).expanduser().resolve(strict=False), "default:preferred-path"))

    candidates.append(((federation_root / repo).resolve(strict=False), "federation-root"))

    for pattern in config.external_root_patterns:
        candidates.append(
            ((resolve_pattern(pattern, config) / repo).resolve(strict=False), "manifest:roots.external")
        )

    env_external_roots = os.environ.get(EXTERNAL_ROOTS_ENV)
    if env_external_roots:
        for pattern in env_external_roots.split(os.pathsep):
            if pattern:
                candidates.append(
                    ((Path(pattern).expanduser().resolve(strict=False) / repo), f"env:{EXTERNAL_ROOTS_ENV}")
                )

    for pattern in DEFAULT_EXTERNAL_ROOT_PATTERNS:
        candidates.append(((Path(pattern).expanduser() / repo).resolve(strict=False), "default:external-root"))

    unique_candidates: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for candidate, origin in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved not in seen:
            seen.add(resolved)
            unique_candidates.append((resolved, origin))
    return unique_candidates


def _is_repo_root(path: Path) -> bool:
    if not path.is_dir():
        return False

    return any(_marker_exists(path / marker) for marker in REPO_MARKERS)


def _marker_exists(path: Path) -> bool:
    return path.is_dir() or path.is_file()
