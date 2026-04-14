from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ..workspace.discovery import Workspace
from .models import ChangeSignal, ChangedPath, MatchedComponent, SurfaceClass
from .registry import RecurrenceRegistry, load_registry, normalize_path


SIGNALS_BY_SURFACE_CLASS: dict[SurfaceClass, list[str]] = {
    "source": ["source_changed"],
    "generated": ["generated_changed"],
    "projected": ["projection_changed"],
    "contract": ["contract_changed"],
    "docs": ["docs_changed"],
    "test": ["tests_changed"],
    "proof": ["proof_changed"],
    "receipt": ["receipt_changed"],
    "other": ["other_changed"],
}


def detect_change_signal(
    workspace: Workspace,
    *,
    repo_root: str,
    diff_base: str | None = None,
    paths: list[str] | None = None,
    registry: RecurrenceRegistry | None = None,
) -> ChangeSignal:
    registry = registry or load_registry(workspace)
    repo_root_path = Path(repo_root).expanduser().resolve()
    repo_name = infer_repo_name(workspace, repo_root_path)
    changed = collect_changed_paths(repo_root_path, diff_base=diff_base, paths=paths)

    changed_path_items: list[ChangedPath] = []
    direct_components: dict[tuple[str, str], MatchedComponent] = {}
    unmatched_paths: list[str] = []

    for rel_path in changed:
        matches = registry.match_path(rel_path)
        matched_refs = [item.component.component_ref for item, _ in matches]
        matched_classes = [surface_class for _, surface_class in matches]
        changed_path_items.append(
            ChangedPath(
                repo=repo_name,
                path=rel_path,
                matched_component_refs=matched_refs,
                matched_classes=matched_classes,
            )
        )
        if not matches:
            unmatched_paths.append(rel_path)
            continue
        for loaded, surface_class in matches:
            key = (loaded.component.component_ref, surface_class)
            existing = direct_components.get(key)
            if existing is None:
                direct_components[key] = MatchedComponent(
                    component_ref=loaded.component.component_ref,
                    owner_repo=loaded.component.owner_repo,
                    match_class=surface_class,
                    matched_paths=[rel_path],
                    inferred_signals=list(SIGNALS_BY_SURFACE_CLASS[surface_class]),
                )
                continue
            existing.matched_paths.append(rel_path)
            for signal in SIGNALS_BY_SURFACE_CLASS[surface_class]:
                if signal not in existing.inferred_signals:
                    existing.inferred_signals.append(signal)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ChangeSignal(
        signal_ref=f"signal:{stamp}:{repo_name}",
        workspace_root=str(workspace.federation_root),
        repo_root=str(repo_root_path),
        repo_name=repo_name,
        observed_at=datetime.now(timezone.utc),
        diff_base=diff_base,
        changed_paths=changed_path_items,
        direct_components=sorted(
            direct_components.values(),
            key=lambda item: (item.owner_repo, item.component_ref, item.match_class),
        ),
        unmatched_paths=sorted(unmatched_paths),
    )


def collect_changed_paths(
    repo_root: Path,
    *,
    diff_base: str | None = None,
    paths: list[str] | None = None,
) -> list[str]:
    if paths:
        return sorted({normalize_path(path) for path in paths if normalize_path(path)})

    if diff_base is None:
        command = ["git", "-C", str(repo_root), "diff", "--name-only", "HEAD"]
    elif diff_base.startswith("git:"):
        spec = diff_base[4:]
        command = ["git", "-C", str(repo_root), "diff", "--name-only", spec]
    else:
        raise ValueError("diff_base must use the form git:<rev-spec> or explicit --path values")

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "unknown git diff failure"
        raise ValueError(f"could not collect changed paths from {repo_root}: {stderr}")

    lines = [normalize_path(line) for line in completed.stdout.splitlines()]
    return sorted({line for line in lines if line})


def infer_repo_name(workspace: Workspace, repo_root: Path) -> str:
    resolved = repo_root.resolve()
    for repo, candidate in workspace.repo_roots.items():
        candidate_resolved = candidate.resolve()
        if resolved == candidate_resolved or candidate_resolved in resolved.parents:
            return repo
    return resolved.name
