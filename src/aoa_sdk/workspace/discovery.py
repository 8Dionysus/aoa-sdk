from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..errors import RepoNotFound
from .roots import KNOWN_REPOS


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
                if (candidate / repo).is_dir()
            }
            if len(repo_roots) >= 2:
                federation_root = candidate
                break

        repo_roots = {
            repo: federation_root / repo
            for repo in KNOWN_REPOS
            if (federation_root / repo).is_dir()
        }
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
