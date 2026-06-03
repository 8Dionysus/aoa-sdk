from __future__ import annotations

from ...workspace.discovery import Workspace
from ..models import ObservationRecord
from ..registry import RecurrenceRegistry
from .common import _evidence, _glob, _obs, _rel, _repo_root


def _collect_generated_staleness(
    workspace: Workspace, registry: RecurrenceRegistry
) -> list[ObservationRecord]:
    producer = "generated_staleness_watch"
    observations: list[ObservationRecord] = []
    counter = 0
    for loaded in registry.iter_components():
        component = loaded.component
        repo_root = _repo_root(workspace, component.owner_repo)
        if repo_root is None or not component.generated_surfaces:
            continue
        sources = _glob(
            repo_root,
            [
                *component.source_inputs,
                *component.contract_surfaces,
                *component.documentation_surfaces,
            ],
        )
        generated = _glob(repo_root, component.generated_surfaces)
        if not sources or not generated:
            continue
        newest_source = max(sources, key=lambda path: path.stat().st_mtime)
        for generated_path in generated:
            if newest_source.stat().st_mtime <= generated_path.stat().st_mtime:
                continue
            counter += 1
            observations.append(
                _obs(
                    producer=producer,
                    counter=counter,
                    component_ref=component.component_ref,
                    owner_repo=component.owner_repo,
                    category="change_pressure",
                    signal="generated_surface_stale",
                    source_inputs=["generated-staleness", "change_signal"],
                    evidence_refs=[
                        _evidence(
                            component.owner_repo,
                            repo_root,
                            newest_source,
                            "#newer-source",
                        ),
                        _evidence(
                            component.owner_repo,
                            repo_root,
                            generated_path,
                            "#stale-generated",
                        ),
                    ],
                    attributes={
                        "source_path": _rel(repo_root, newest_source),
                        "generated_path": _rel(repo_root, generated_path),
                        "source_mtime": newest_source.stat().st_mtime,
                        "generated_mtime": generated_path.stat().st_mtime,
                    },
                    notes="source/contract/docs surface is newer than a generated surface; review regeneration before downstream projection",
                )
            )
    return observations
