# Checkpoint No-Closeout Session Reconcile

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0062
- Original date: 2026-06-03
- Surface classes: checkpoint, lifecycle, runtime-evidence, generated-index, validation
- SDK facets: checkpoint control-plane, session-memory attachment, CLI facade
- Mechanic parents: checkpoint
- Guard families: checkpoint lifecycle, pending review, session-memory boundary, generated navigation
- Posture: accepted

## Context

Checkpoint scopes can remain under `.aoa/session-growth/current/` after the
operator closes a Codex session without running the reviewed closeout cycle.
The previous lifecycle route could close/archive reviewed closeout-executed
scopes and move stale nonpending evidence, but it could not distinguish a
session-memory-backed no-closeout ending from an ordinary stale scope.

That gap made two bad outcomes likely: old checkpoint evidence stayed noisy in
`current/`, or a cleanup pass moved it without recording that reviewed closeout
never happened.

## Options Considered

- Keep using `close-archive --include-stale` for every old scope.
- Add a hidden daemon that infers closeout and cleanup automatically.
- Make aoa-session-memory responsible for checkpoint lifecycle cleanup.
- Add an explicit bounded reconcile/sweep route in checkpoint lifecycle.

## Decision

Add checkpoint session reconciliation as a bounded control-plane route.

`aoa checkpoint reconcile-sessions` and
`aoa checkpoint sweep-closed-sessions` dry-run by default. They read
aoa-session-memory archive refs from the checkpoint runtime-session trace,
classify ended sessions as `session_closed_pending_review`,
`session_closed_reviewed_no_closeout`, or
`session_closed_collecting_no_closeout`, and only with `--apply` move
nonpending no-closeout scopes to archive with a
`checkpoint_session_archived_without_closeout_v1` lifecycle event.

Closeout-executed compatibility stays available through the same sweep route,
but `archived_without_closeout` is not `closed`. Pending-review scopes report a
required action and remain in `current/`.

The route also writes a generated checkpoint lifecycle navigation index with
lifecycle entries, unresolved review, session-memory refs, repo/candidate/commit
lookups, and graph-ready anchors/edges. That index is navigation only; it is
not durable memory, proof, progression truth, or a RAG engine.

## Rationale

The SDK owns checkpoint control-plane visibility, not session-memory truth or
reviewed closeout meaning. Reading aoa-session-memory refs lets checkpoint
cleanup know when a session really ended, while preserving the owner boundary:
the memory archive stays read-only evidence and the SDK does not mutate it.

A hidden daemon would blur review, closeout, and owner authority. A dry-run
sweeper keeps the operation explicit, testable, and safe to wrap later in a
bounded timer if the operator wants automation.

## Consequences

- `current/` can become active-now or still-actionable again without losing
  no-closeout evidence.
- Session-memory-backed closed sessions get a distinct lifecycle state instead
  of being flattened into stale scope or reviewed closeout.
- Pending checkpoint review remains a hard block.
- GraphRAG preparation gets anchors and edges without turning `aoa-sdk` into a
  retrieval or memory owner.

## Source Surfaces

- `src/aoa_sdk/checkpoints/reconcile.py`
- `src/aoa_sdk/checkpoints/lifecycle.py`
- `src/aoa_sdk/checkpoints/session_memory.py`
- `src/aoa_sdk/checkpoints/indexes.py`
- `src/aoa_sdk/contracts/checkpoints.py`
- `src/aoa_sdk/cli/checkpoint.py`
- `src/aoa_sdk/cli/rendering.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/`
- `mechanics/checkpoint/README.md`

## Follow-Up Route

Use `reconcile-sessions --dry-run` before applying no-closeout archive
movement. If later automation is needed, wrap the same bounded command; do not
add hidden closeout, review, harvest, memory, or owner actions.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
