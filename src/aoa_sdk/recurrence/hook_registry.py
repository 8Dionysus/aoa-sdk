from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..workspace.discovery import Workspace
from .models import HookBinding, HookBindingSet, HookEvent


@dataclass(slots=True)
class LoadedHookBindingSet:
    manifest_path: Path
    binding_set: HookBindingSet


class HookRegistry:
    def __init__(self, workspace: Workspace, loaded: list[LoadedHookBindingSet]) -> None:
        self.workspace = workspace
        self.loaded = loaded
        self.by_ref = {
            binding.binding_ref: binding
            for item in loaded
            for binding in item.binding_set.bindings
        }

    def get(self, binding_ref: str) -> HookBinding | None:
        return self.by_ref.get(binding_ref)

    def iter_bindings(
        self,
        *,
        event: HookEvent | None = None,
        owner_repo: str | None = None,
        component_ref: str | None = None,
    ) -> Iterable[HookBinding]:
        for item in self.loaded:
            binding_set = item.binding_set
            for binding in binding_set.bindings:
                if event is not None and binding.event != event:
                    continue
                if owner_repo is not None and binding.owner_repo != owner_repo:
                    continue
                if component_ref is not None and binding.component_ref != component_ref:
                    continue
                yield binding


def load_hook_registry(workspace: Workspace) -> HookRegistry:
    loaded: list[LoadedHookBindingSet] = []
    for repo, repo_root in workspace.repo_roots.items():
        hook_root = repo_root / "manifests" / "recurrence" / "hooks"
        if not hook_root.is_dir():
            continue
        for path in sorted(hook_root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            binding_set = HookBindingSet.model_validate(payload)
            if binding_set.owner_repo != repo:
                binding_set = binding_set.model_copy(update={"owner_repo": repo})

            repaired_bindings: list[HookBinding] = []
            changed = False
            for binding in binding_set.bindings:
                updates = {}
                if binding.owner_repo != repo:
                    updates["owner_repo"] = repo
                if not binding.component_ref:
                    updates["component_ref"] = binding_set.component_ref
                if updates:
                    binding = binding.model_copy(update=updates)
                    changed = True
                repaired_bindings.append(binding)

            if changed:
                binding_set = binding_set.model_copy(update={"bindings": repaired_bindings})
            loaded.append(LoadedHookBindingSet(manifest_path=path, binding_set=binding_set))
    return HookRegistry(workspace, loaded)
