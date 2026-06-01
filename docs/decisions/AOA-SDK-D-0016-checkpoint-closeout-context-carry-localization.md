# Checkpoint Closeout Context Carry Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0016
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, checkpoint, reviewed closeout context carry
- Mechanic parents: checkpoint
- Guard families: mechanics topology, part validation, docs routes, active naming
- Posture: accepted

## Context

After the RPG localization slice, Checkpoint still carried reviewed closeout
context payload in root districts:

- `docs/CANDIDATE_LINEAGE_CARRY.md`
- `docs/closeout-followthrough-map.md`
- `docs/COMPONENT_DRIFT_HINTS.md`
- `docs/SELF_AGENCY_CONTINUITY_CARRY.md`
- `docs/SESSION_GROWTH_KERNEL_SIGNAL_RULES.md`
- closeout-carry schemas under `schemas/`
- closeout-carry examples under `examples/`
- candidate-lineage and component-refresh tests under `tests/`

Those surfaces share one route: after reviewed checkpoint/closeout reread, the
SDK may carry advisory packets for owner followthrough, component-refresh
pressure, continuity hints, and next-kernel selection. It must not mint
candidate, seed, object, continuity, refresh, memory, proof, progression, or
owner-acceptance truth.

## Decision

Localize the reviewed closeout context payload into:

- `mechanics/checkpoint/parts/reviewed-closeout-context-carry/`

Keep session checkpoint capture, reviewed session handoff runner behavior, git hooks, and the
importable `src/aoa_sdk/checkpoints/`, `src/aoa_sdk/closeout/`, and
`src/aoa_sdk/a2a/` source homes in their existing routes until a later slice
proves a narrower owner.

## Rationale

The old root doc titles named topics and historical entrypoints. The active
part name says the operational map:

- `reviewed`: the packet is built after reread, not from raw session drift
- `closeout`: the input is closeout/checkpoint context
- `context-carry`: the output is advisory carry, not owner truth

This matches the agent-facing topology rule: role, input, output, owner, next
route, and validation should be visible in the active path. Legacy names stay
in provenance and migration accounting only.

## Consequences

- Root `docs/`, `schemas/`, `examples/`, and `tests/` no longer own active
  closeout context carry payload.
- The Checkpoint mechanic now has an active `reviewed-closeout-context-carry`
  part beside `child-task-reentry`.
- Root route docs point at the part-local path instead of old root filenames.
- Old root names live in `mechanics/checkpoint/PROVENANCE.md` and
  `mechanics/ARTIFACT_TOPOLOGY.md`, not as active fallbacks.
- Stronger owner repositories still decide landing, repair, refresh, memory,
  proof, progression, continuity, and execution truth.

## Source Surfaces

- `mechanics/checkpoint/README.md`
- `mechanics/checkpoint/PARTS.md`
- `mechanics/checkpoint/PROVENANCE.md`
- `mechanics/checkpoint/parts/reviewed-closeout-context-carry/`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `README.md`
- `ROADMAP.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md`

## Follow-Up Route

Continue root technical district audit for remaining Checkpoint capture and
review-note payload, release-support, skill-runtime and boundary-bridge
surface access, Codex Projection workspace MCP, Questbook payload, and
cross-mechanic public contracts.

## Verification

```bash
python -m pytest -q mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_reviewed_closeout_context_carry.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_component_refresh_followthrough.py
python scripts/validate_mechanics_topology.py
```
