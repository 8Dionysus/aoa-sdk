# CLI Surface Test Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0028
- Original date: 2026-06-01
- Surface classes: topology, mechanics, test placement, CLI
- SDK facets: mechanics topology, runtime seam, boundary bridge
- Mechanic parents: runtime-seam, boundary-bridge
- Guard families: mechanics topology, part validation, active naming, root-surface hygiene
- Posture: accepted

## Context

Root `tests/test_cli.py` kept several unrelated active surfaces together:

- workspace inspect commands
- portable workspace bootstrap commands
- compatibility check commands
- skill detection, dispatch, enter, and guard commands

Those commands share a Typer app, but they do not share one owner operation.
Keeping them under a root CLI filename hid the route map that future agents
need: Runtime Seam owns workspace path/bootstrap behavior; Boundary Bridge owns
consumed-surface compatibility posture and skill runtime reporting.

## Decision

Move the CLI tests into owner parts:

- `mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py`
- `mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests/test_portable_workspace_bootstrap_cli.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py`
- `mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py`

Create the Runtime Seam part `portable-workspace-bootstrap` because bootstrap
already has real SDK source, CLI behavior, fixtures, mutation boundaries, and
validation pressure. Keep `src/aoa_sdk/cli/` as the importable cross-mechanic
CLI facade.

## Rationale

The active file names now expose role, input, output, owner, and validation:

- workspace root inspection resolves paths;
- portable workspace bootstrap prepares a non-default workspace without owning
  sibling content;
- consumed-surface posture CLI reports compatibility safely;
- skill runtime bridge CLI reports actionability below `aoa-skills` meaning.

This matches the mechanics topology rule: single-mechanic payload belongs to
the owning part, while shared SDK source remains in `src/aoa_sdk/`.

## Consequences

- Root `tests/test_cli.py` no longer exists as an active route.
- Runtime Seam active routes now include `portable-workspace-bootstrap`.
- Boundary Bridge validation includes CLI proof under the same parts that own
  the non-CLI behavior.
- The old root CLI filename is provenance only in artifact and package
  provenance ledgers.

## Source Surfaces

- `mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py`
- `mechanics/runtime-seam/parts/portable-workspace-bootstrap/`
- `mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests/test_portable_workspace_bootstrap_cli.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py`
- `mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py`
- `src/aoa_sdk/cli/`
- `src/aoa_sdk/workspace/bootstrap.py`
- `src/aoa_sdk/compatibility/`
- `src/aoa_sdk/skills/`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`

## Follow-Up Route

Continue the root test audit for repo-wide validators only: decision indexes,
design surfaces, docs routes, mechanics topology, sibling canary, smoke, and
nested AGENTS validation.

## Verification

```bash
python -m pytest -q mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests/test_portable_workspace_bootstrap_cli.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py
python scripts/validate_mechanics_topology.py
python scripts/generate_decision_indexes.py --check
python -m ruff check .
```
