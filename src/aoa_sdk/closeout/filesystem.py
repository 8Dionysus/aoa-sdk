from __future__ import annotations

from pathlib import Path
import re
import shutil


def default_closeout_root(self) -> Path:
    return self.workspace.repo_path("aoa-sdk") / ".aoa" / "closeout"

def default_queue_paths(self) -> dict[str, Path]:
    root = self.default_closeout_root()
    return {
        "root": root,
        "requests": root / "requests",
        "manifests": root / "manifests",
        "inbox": root / "inbox",
        "processed": root / "processed",
        "failed": root / "failed",
        "reports": root / "reports",
        "handoffs": root / "handoffs",
    }

def _resolve_queue_dir(self, candidate: str | Path | None, *, leaf: str) -> Path:
    if candidate is None:
        return self.default_closeout_root() / leaf
    return Path(candidate).expanduser().resolve()

def _resolve_existing_path(self, manifest_path: Path, item: str) -> Path:
    path = Path(item).expanduser()
    if not path.is_absolute():
        path = (manifest_path.parent / path).resolve()
    else:
        path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"missing closeout input: {path}")
    return path

def _resolve_input_paths(self, manifest_path: Path, input_paths: list[str]) -> list[Path]:
    resolved: list[Path] = []
    for item in input_paths:
        resolved.append(self._resolve_existing_path(manifest_path, item))
    return resolved

def _resolve_optional_paths(self, manifest_path: Path, input_paths: list[str]) -> list[str]:
    resolved: list[str] = []
    for item in input_paths:
        path = Path(item).expanduser()
        if not path.is_absolute():
            path = (manifest_path.parent / path).resolve()
        else:
            path = path.resolve()
        resolved.append(str(path))
    return resolved

def _archive_manifest(self, manifest_path: Path, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    candidate = destination_dir / manifest_path.name
    if candidate.exists():
        stem = manifest_path.stem
        suffix = manifest_path.suffix
        counter = 1
        while candidate.exists():
            candidate = destination_dir / f"{stem}-{counter}{suffix}"
            counter += 1
    shutil.move(str(manifest_path), str(candidate))
    return candidate

def _latest_path(self, paths: list[Path]) -> str | None:
    if not paths:
        return None
    latest = max(paths, key=lambda path: path.stat().st_mtime)
    return str(latest)

def _safe_closeout_filename(self, closeout_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", closeout_id).strip("-")
    return safe or "closeout"

def _unique_strings(self, items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique

def _unique_paths(self, items: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for item in items:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique

def _derive_closeout_id(self, session_ref: str) -> str:
    return f"closeout-{self._safe_closeout_filename(session_ref)}"
