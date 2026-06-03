# Low-Pressure Route Stop-Lines

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0060
- Original date: 2026-06-03
- Surface classes: source-topology, implementation, validation, stop-line
- SDK facets: importable implementation, route-role branches, compatibility re-export
- Mechanic parents: checkpoint, recurrence, release-support, boundary-bridge
- Guard families: source topology, route-role pressure, stop-line discipline
- Posture: accepted

## Context

After the checkpoint, CLI, closeout, recurrence, and shared-contract cuts, the
source-topology index still names several low-pressure modules in the largest
module list:

- `src/aoa_sdk/checkpoints/ledger/notes.py`
- `src/aoa_sdk/release/api.py`
- `src/aoa_sdk/skills/detector.py`
- `src/aoa_sdk/compatibility/policy.py`
- `src/aoa_sdk/recurrence/hooks.py`

These files are not clean split targets merely because they are visible. Each
already sits inside an owning route branch and remains below medium split
pressure.

## Decision

Keep these modules as explicit stop-lines for this landing:

- `checkpoints/ledger/notes.py` remains the checkpoint ledger assembly,
  rotation, runtime note loading, and session-end derivation owner.
- `release/api.py` remains the bounded release audit/publish helper API.
- `skills/detector.py` remains the skill detection, host-availability, and
  checkpoint bridge detection owner.
- `compatibility/policy.py` remains the consumed-surface compatibility policy
  owner.
- `recurrence/hooks.py` remains the recurrence hook binding/run owner.

Do not split them without evidence of a new owner route. File size alone is not
enough.

## Rationale

The purpose of this pass is to cut route-role mixtures, not to maximize module
count. Splitting low-pressure files without a named owner would create more
topology noise and weaker routing.

## Consequences

- The remaining modules are documented as intentional keep surfaces.
- Future changes must name the new route-role pressure before splitting one of
  these files.
- The source-topology index carries explicit next-route stop-line text for the
  kept modules.

## Source Surfaces

- `src/aoa_sdk/checkpoints/ledger/notes.py`
- `src/aoa_sdk/release/api.py`
- `src/aoa_sdk/skills/detector.py`
- `src/aoa_sdk/compatibility/policy.py`
- `src/aoa_sdk/recurrence/hooks.py`
- `generated/source_topology.min.json`
- `tests/test_source_topology_index.py`

## Follow-Up Route

If one of these files grows again, first identify the new owner branch. Only
then cut the module and update source topology, decisions, and targeted tests
together.

## Verification

```bash
python scripts/build_source_topology_index.py --check
python scripts/validate_source_topology_index.py
python -m pytest -q tests/test_source_topology_index.py
python scripts/release_check.py
```
