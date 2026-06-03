# CLI Command Family Route Modules

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0056
- Original date: 2026-06-03
- Surface classes: source-topology, cli, implementation, validation
- SDK facets: importable implementation, CLI command surface, route-role branches
- Mechanic parents: boundary-bridge, checkpoint, release-support, runtime-seam
- Guard families: source topology, CLI compatibility, command-family routing
- Posture: accepted

## Context

`src/aoa_sdk/cli/main.py` owned the root Typer app, every sub-app, all
command implementations, shared path and persistence helpers, checkpoint hook
argument resolution, host-skill manifest parsing, and human-readable rendering.

That made the CLI entrypoint the highest-pressure SDK implementation module.
The problem was not only size: new command behavior could land in one broad
file without routing through the mechanic or SDK facet it actually served.

## Options Considered

- Keep `cli/main.py` as the single CLI implementation module.
- Split only rendering helpers and leave all commands in `main.py`.
- Move command implementations into mechanic packages.
- Keep one public CLI entrypoint and split command families under
  `src/aoa_sdk/cli/`.

## Decision

Keep `src/aoa_sdk/cli/main.py` as the public Typer app assembly surface and
move command behavior into command-family route modules:

- `cli/workspace.py` owns workspace inspect and bootstrap commands.
- `cli/compatibility.py` owns consumed-surface compatibility checks.
- `cli/skills.py` owns skill detect, dispatch, enter, and guard commands.
- `cli/surfaces.py` owns surface detect and handoff commands.
- `cli/checkpoint.py` owns checkpoint append, mark, review, hook, boundary,
  promotion, and checkpoint-closeout bridge commands.
- `cli/closeout.py` owns reviewed closeout run, manifest, queue, inbox, and
  status commands.
- `cli/release.py` owns release audit and publish commands.
- `cli/common.py` owns shared CLI path resolution, persistence, host-skill
  manifest parsing, and checkpoint hook argument normalization.
- `cli/rendering.py` owns human-readable CLI report rendering.

`main.py` still exposes `app` for console scripts and tests. It also keeps the
legacy private `_resolve_checkpoint_hook_repos` re-export used by the existing
checkpoint CLI tests.

## Rationale

The CLI is a control-plane surface, not an owner of sibling meaning. Splitting
by command family keeps command registration close to the route it serves while
preserving one stable `aoa` console entrypoint.

Shared rendering and path/persistence helpers remain in CLI-specific modules
because they are presentation and CLI plumbing, not checkpoint, surface,
skill, release, or closeout domain authority.

## Consequences

- Public `aoa_sdk.cli.main:app` and `aoa` console behavior remain stable.
- New commands should land in the command-family module that owns the route.
- `main.py` should stay app assembly only.
- Shared CLI output formatting belongs in `cli/rendering.py`.
- Shared CLI path, write, load, host-skill, and hook argument plumbing belongs
  in `cli/common.py`.
- Route modules should call SDK APIs instead of becoming owner semantics.

## Source Surfaces

- `src/aoa_sdk/cli/main.py`
- `src/aoa_sdk/cli/common.py`
- `src/aoa_sdk/cli/rendering.py`
- `src/aoa_sdk/cli/workspace.py`
- `src/aoa_sdk/cli/compatibility.py`
- `src/aoa_sdk/cli/skills.py`
- `src/aoa_sdk/cli/surfaces.py`
- `src/aoa_sdk/cli/checkpoint.py`
- `src/aoa_sdk/cli/closeout.py`
- `src/aoa_sdk/cli/release.py`
- `src/aoa_sdk/recurrence/cli.py`
- `generated/source_topology.min.json`
- `tests/test_source_topology_index.py`

## Follow-Up Route

Do not add command implementations to `main.py`. Add or change command
behavior in the owning `cli/*` command-family module, and move non-CLI domain
logic back into the SDK facade or mechanic branch that owns it.

`recurrence/cli.py` remains a mechanic-local CLI surface for now because its
split pressure is still on the recurrence route itself, not on root CLI app
assembly.

## Verification

```bash
python -m ruff check src/aoa_sdk/cli
python -m mypy src/aoa_sdk/cli
python -m aoa_sdk.cli.main --help
python -m pytest -q mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests/test_portable_workspace_bootstrap_cli.py mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py
python scripts/build_source_topology_index.py --check
python scripts/validate_source_topology_index.py
python -m pytest -q tests/test_source_topology_index.py
python scripts/release_check.py
```
