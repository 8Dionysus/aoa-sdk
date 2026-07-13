# Checkpoint Skipped Session Recovery Branch

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0055
- Original date: 2026-06-03
- Surface classes: source-topology, checkpoint, implementation, validation
- SDK facets: importable implementation, checkpoint control-plane, route-role branches
- Mechanic parents: checkpoint
- Guard families: source topology, checkpoint route roles, skipped-session recovery
- Posture: accepted

## Context

The post-commit checkpoint path can request manual review while no active
runtime session exists. That state is valid and must remain blocking until an
agent explicitly recovers and reviews the checkpoint note.

The recovery behavior landed as fresh checkpoint logic around
`CheckpointsAPI.review_note()` and `CheckpointsAPI.git_boundary_check()`. That
fixed the boundary behavior, but it also put a new route-role family back into
`src/aoa_sdk/checkpoints/registry.py`, which is meant to remain the public
facade and route-role orchestrator.

## Options Considered

- Keep skipped-session recovery helpers in `registry.py`.
- Fold recovery into `review/after_commit.py`.
- Fold recovery into `review/agent_review.py`.
- Create a named checkpoint review branch for skipped-session recovery.

## Decision

Keep `src/aoa_sdk/checkpoints/registry.py` as the public `CheckpointsAPI`
facade and move skipped-session recovery behavior to
`src/aoa_sdk/checkpoints/review/skipped_recovery.py`.

The skipped-session recovery branch owns:

- loading the latest post-commit status report;
- detecting unresolved skipped post-commit reports;
- matching a skipped report to the requested commit and session file;
- checking whether a skipped thread-scoped report is still reachable from
  `HEAD`;
- rendering the blocking required action for push and merge boundaries;
- recreating the runtime session and replaying `after_commit()` for
  `review-note --auto`.

`CheckpointsAPI` keeps the public method shape, CLI compatibility, and
orchestration. It does not own the recovery rules themselves.

## Rationale

Skipped-session recovery is not generic after-commit report writing and not
generic agent-review autofill. It is a boundary repair route between an
unresolved status report, a thread-scoped runtime session file, and the
post-commit review path.

Keeping that route named gives future agents a clean destination for changes to
`review-note --auto`, `git-boundary-check`, and hook-facing skipped checkpoint
behavior without widening the checkpoint facade again.

## Consequences

- Public imports and CLI behavior remain stable.
- `registry.py` delegates skipped-session recovery to the owning review branch.
- `review/after_commit.py` remains focused on report creation and
  auto-observation material.
- `review/agent_review.py` remains focused on review autofill and review carry.
- Future skipped-session changes must update this branch, targeted checkpoint
  tests, and the source-topology index together.

## Source Surfaces

- `src/aoa_sdk/checkpoints/registry.py`
- `src/aoa_sdk/checkpoints/review/skipped_recovery.py`
- `src/aoa_sdk/checkpoints/review/after_commit.py`
- `src/aoa_sdk/checkpoints/review/agent_review.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/`
- `generated/source_topology.min.json`
- `tests/test_source_topology_index.py`

## Follow-Up Route

Do not add more skipped-session logic to `registry.py`. Route recovery,
matching, reachability, and required-action wording into
`review/skipped_recovery.py`. Route report construction back to
`review/after_commit.py` and review summary/carry logic back to
`review/agent_review.py`.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
