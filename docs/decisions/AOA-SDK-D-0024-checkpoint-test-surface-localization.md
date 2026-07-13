# Checkpoint Test Surface Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0024
- Original date: 2026-06-01
- Surface classes: topology, mechanics, test placement
- SDK facets: mechanics topology, checkpoint, CLI
- Mechanic parents: checkpoint
- Guard families: mechanics topology, active naming, root-surface hygiene
- Posture: accepted

## Context

After the Checkpoint docs and runner scripts moved under part-local homes,
root `tests/` still carried active Checkpoint tests:

- `tests/test_checkpoint_cli.py`
- `tests/test_checkpoints.py`
- `tests/test_closeout.py`
- `tests/test_dirty_gate.py`
- closeout CLI cases inside `tests/test_cli.py`

Those tests are not repo-wide smoke tests. They validate active Checkpoint
parts and should therefore live with their owning part.

## Decision

Move session-growth checkpoint API/CLI tests into:

- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/`

Move reviewed-session handoff runner API/CLI tests into:

- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/`

At this slice, non-Checkpoint CLI cases remained for a later owner split.
AOA-SDK-D-0028 moves those cases into Runtime Seam and Boundary Bridge parts.

## Rationale

The active test path should reveal the operation under test. A root
`tests/test_closeout.py` filename says only "legacy command family"; the part
path says the real route: reviewed session handoff runner. Likewise, checkpoint
capture/review tests belong to the session-growth checkpoint cycle, not to an
anonymous root test bucket.

## Consequences

- Root `tests/` no longer owns Checkpoint active test homes.
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/` now carries
  both the docs and API/CLI proof for session-local checkpoint capture and
  review.
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/` now carries
  the runner API/CLI proof, including the closeout CLI cases formerly embedded
  in root CLI tests.
- Cross-mechanic references may import the part-local fixture only as test
  support; they must not make the Boundary Bridge own Checkpoint runner truth.

## Source Surfaces

- `mechanics/checkpoint/README.md`
- `mechanics/checkpoint/AGENTS.md`
- `mechanics/checkpoint/PROVENANCE.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/VALIDATION.md`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/VALIDATION.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py`
- `mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge.py`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`

## Follow-Up Route

Continue root technical district audit for remaining SDK-wide versus
part-owned tests and for non-test root contracts that still need explicit owner
classification.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
