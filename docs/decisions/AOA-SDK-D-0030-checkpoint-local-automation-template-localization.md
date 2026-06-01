# Checkpoint Local Automation Template Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0030
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, local automation
- SDK facets: mechanics topology, checkpoint, managed hooks, closeout runner
- Mechanic parents: checkpoint
- Guard families: mechanics topology, active naming, root-surface hygiene
- Posture: accepted

## Context

Root `githooks/` and `systemd/` still carried active Checkpoint payload after
the main mechanics localization:

- managed checkpoint hook templates for `post-commit`, `pre-push`, and
  `pre-merge-commit`
- closeout inbox user units for `aoa-closeout-inbox.path` and
  `aoa-closeout-inbox.service`

The filenames are imposed by Git and systemd, but the owner route is not root.
The hooks belong to `session-growth-checkpoint-cycle`; the user units belong to
`reviewed-session-handoff-runner`.

## Decision

Move the local automation templates into part-local homes:

- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/`

Update hook template lookup and closeout unit installation to use those
part-local paths.

## Rationale

Git and systemd names should stay native because they are the external tool
contracts. The active owner path around those filenames must still be
topological: what operation owns the template, what it is allowed to trigger,
and which validation route proves it.

## Consequences

- Root `githooks/` and `systemd/` no longer carry active mechanic payload.
- Managed hook template lookup now reads the session-growth checkpoint part.
- Closeout unit installation now reads the reviewed-session handoff runner
  part.
- `DESIGN.md` and `DESIGN.AGENTS.md` now name part-local local-automation
  routes instead of root local-automation districts.
- Root local automation references remain only in provenance, decisions, or
  external tool vocabulary.

## Source Surfaces

- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/`
- `src/aoa_sdk/checkpoints/registry.py`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/scripts/install_closeout_units.py`
- `mechanics/checkpoint/README.md`
- `mechanics/checkpoint/PROVENANCE.md`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `mechanics/topology.json`

## Follow-Up Route

Keep external-tool filenames native, but keep their active owner route
part-local. Do not reintroduce root hook or unit fallback homes.

## Verification

```bash
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py
python scripts/validate_nested_agents.py
python scripts/validate_mechanics_topology.py
```
