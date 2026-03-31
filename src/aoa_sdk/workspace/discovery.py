from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..errors import RepoNotFound
from .roots import (
    EXTERNAL_ROOT_PATTERNS,
    KNOWN_REPOS,
    PREFERRED_REPO_PATH_PATTERNS,
    REPO_MARKERS,
)


@dataclass(slots=True)
class Workspace:
    root: Path
    federation_root: Path
    repo_roots: dict[str, Path]

    @classmethod
    def discover(cls, root: str | Path) -> "Workspace":
        resolved = Path(root).expanduser().resolve()
        start = resolved if resolved.is_dir() else resolved.parent

        federation_root = start
        for candidate in (start, *start.parents):
            repo_roots = {
                repo: candidate / repo
                for repo in KNOWN_REPOS
                if _is_repo_root(candidate / repo)
            }
            if len(repo_roots) >= 2:
                federation_root = candidate
                break

        repo_roots = {}
        for repo in KNOWN_REPOS:
            path = _discover_repo_path(repo=repo, federation_root=federation_root)
            if path is not None:
                repo_roots[repo] = path
        return cls(root=start, federation_root=federation_root, repo_roots=repo_roots)

    def has_repo(self, repo: str) -> bool:
        return repo in self.repo_roots

    def repo_path(self, repo: str) -> Path:
        path = self.repo_roots.get(repo)
        if path is None:
            raise RepoNotFound(f"Repository {repo!r} is not available under {self.federation_root}")
        return path

    def surface_path(self, repo: str, relative_path: str | Path) -> Path:
        return self.repo_path(repo) / Path(relative_path)


def _discover_repo_path(*, repo: str, federation_root: Path) -> Path | None:
    for candidate in _repo_candidates(repo=repo, federation_root=federation_root):
        if _is_repo_root(candidate):
            return candidate
    return None


def _repo_candidates(*, repo: str, federation_root: Path) -> list[Path]:
    candidates: list[Path] = []

    for pattern in PREFERRED_REPO_PATH_PATTERNS.get(repo, ()):
        candidates.append(Path(pattern).expanduser())

    candidates.append(federation_root / repo)

    for pattern in EXTERNAL_ROOT_PATTERNS:
        candidates.append(Path(pattern).expanduser() / repo)

    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved not in seen:
            seen.add(resolved)
            unique_candidates.append(resolved)
    return unique_candidates


def _is_repo_root(path: Path) -> bool:
    if not path.is_dir():
        return False

    return any(_marker_exists(path / marker) for marker in REPO_MARKERS)


def _marker_exists(path: Path) -> bool:
    return path.is_dir() or path.is_file()
