# Checkpoint Lifecycle Close Archive

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0061
- Original date: 2026-06-03
- Surface classes: checkpoint, implementation, lifecycle, runtime-evidence, validation
- SDK facets: checkpoint control-plane, importable implementation, session-memory attachment
- Mechanic parents: checkpoint
- Guard families: checkpoint lifecycle, pending review, source topology, session-memory boundary
- Posture: accepted

## Context

Checkpoint runtime scopes under `.aoa/session-growth/current/` had accumulated
long after their sessions were no longer active. The existing mechanic could
capture, review, build closeout context, and execute closeout bridge artifacts,
but it did not expose a first-class lifecycle route that separated active work
from pending review, reviewed but unclosed closeout, completed closeout, and
stale evidence.

This made `current/` noisy and weakened agent routing: a future agent could
mistake old reviewed scopes for active work or clean them up without preserving
why they were safe to move.

## Options Considered

- Leave lifecycle cleanup as an implicit side effect of future checkpoint
  capture.
- Delete old `current/` scopes as workspace noise.
- Move stale scopes by ad hoc filesystem commands.
- Add an explicit checkpoint lifecycle audit and close/archive route.

## Decision

Add a checkpoint lifecycle branch owned by
`src/aoa_sdk/checkpoints/lifecycle.py`.

The branch classifies current checkpoint scopes as:

- `active_current`
- `pending_review`
- `reviewed_awaiting_closeout`
- `closeout_built`
- `closeout_executed`
- `closed`
- `stale_current_scope`

`aoa checkpoint lifecycle-audit` reports that state without moving files.
`aoa checkpoint close-archive` previews by default. With `--apply`, it closes
reviewed, nonpending, closeout-executed scopes by appending a
`checkpoint_lifecycle_closed_v1` event to the JSONL ledger, rebuilding
snapshots, and moving the scope under `.aoa/session-growth/archive/`. Already
`closed` or `promoted` runtime-scoped ledgers are archiveable by `--apply`
without appending another close event.

With `--include-stale`, the command may move nonpending stale current scopes as
archive evidence without marking them closed. Pending-review scopes remain
blocked even when closeout artifacts exist nearby.

Session-memory refs read from closeout context or execution reports stay
read-only route evidence. The checkpoint lifecycle route must not mutate
aoa-session-memory or turn generated memory indexes into reviewed truth.

## Rationale

Checkpoint is a control-plane ledger and bridge. Its lifecycle route should
make local evidence state legible, not claim memory, proof, progression, quest,
or owner truth.

Append-only closure preserves the reason a reviewed closeout scope left
`current/`. Separate stale archive movement keeps old evidence available while
not pretending that every old scope completed reviewed closeout.

Keeping this behavior in a named lifecycle module finishes the pressure that
remained in `registry.py`: `CheckpointsAPI` can stay the public facade while
route-role behavior lives in the branch that owns it.

## Consequences

- `current/` is again meaningful as active runtime scope or still-actionable
  checkpoint state.
- Reviewed closeout execution has a deterministic close/archive path.
- Pending review remains a hard stop-line for close/archive and promotion.
- Session-memory archive refs can strengthen evidence routing without widening
  SDK authority over memory.
- Future lifecycle states need a new named route and tests, not ad hoc cleanup.

## Source Surfaces

- `src/aoa_sdk/checkpoints/lifecycle.py`
- `src/aoa_sdk/checkpoints/registry.py`
- `src/aoa_sdk/checkpoints/ledger/notes.py`
- `src/aoa_sdk/checkpoints/ledger/lifecycle_events.py`
- `src/aoa_sdk/contracts/checkpoints.py`
- `src/aoa_sdk/cli/checkpoint.py`
- `src/aoa_sdk/cli/rendering.py`
- `mechanics/checkpoint/README.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/`
- `generated/source_topology.min.json`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/`

## Follow-Up Route

Use lifecycle audit before touching accumulated checkpoint state. If a future
route needs stronger closure semantics, add the state through the lifecycle
branch and update checkpoint route cards, source topology, and focused tests in
the same slice.

## Verification

```bash
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_session_memory.py
python scripts/build_source_topology_index.py --check
python scripts/validate_source_topology_index.py
python -m pytest -q tests/test_source_topology_index.py tests/test_docs_routes.py
aoa checkpoint lifecycle-audit /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json
aoa checkpoint close-archive /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json
python scripts/release_check.py
```
