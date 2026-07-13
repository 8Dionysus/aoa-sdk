# Checkpoint Backlog Runtime Trace Gaps

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0065
- Original date: 2026-06-04
- Surface classes: checkpoint, lifecycle, session-memory, generated-index, validation
- SDK facets: checkpoint control-plane, session-memory attachment, CLI facade, source topology
- Mechanic parents: checkpoint
- Guard families: checkpoint lifecycle, session-memory boundary, generated navigation, no hidden automation
- Posture: accepted

## Context

Checkpoint lifecycle and no-closeout reconcile can already distinguish active
scopes, pending review, reviewed closeout execution, stale current evidence,
and session-memory-backed no-closeout endings.

The live backlog still exposed a weaker gap: an SDK-local runtime-session trace
may point at a Codex thread and raw rollout path, while aoa-session-memory does
not yet expose a matching archive ref. Treating that as ordinary stale noise
loses the route. Treating it as reconcile-ready overclaims session-memory
evidence.

## Options Considered

- Keep `lifecycle-audit` and `reconcile-sessions` as the only inspection routes.
- Add a daemon or timer that sweeps old checkpoint scopes automatically.
- Make aoa-session-memory mutate or classify checkpoint scopes.
- Add a read-only backlog audit that names runtime trace gaps and next routes.

## Decision

Add checkpoint backlog audit as a bounded read-only route.

`aoa checkpoint backlog-audit` reads checkpoint lifecycle entries, resolves
SDK-local runtime-session trace refs, reports session-memory archive status,
raw refs, required actions, and next routes, and can write:

```text
.aoa/session-growth/indexes/checkpoint-backlog-navigation.min.json
```

The backlog index groups open scopes by repo, lifecycle state, next route,
runtime trace status, and session-memory status. It also records graph-ready
anchors for checkpoint notes, runtime traces, Codex threads, raw refs,
session-memory archives, and next routes.

Runtime trace refs are evidence coordinates only. They can route
aoa-session-memory freshness, sweep, import, or recovery checks, but they do
not prove that a session-memory archive exists and do not make a checkpoint
scope reconcile-ready by themselves.

## Rationale

Backlog audit answers a different question than reconcile.

Reconcile asks: "Which nonpending checkpoint scopes have enough
session-memory-backed no-closeout evidence to archive?"

Backlog audit asks: "What is still open, why is it open, and which route should
handle it next?"

Keeping that question read-only preserves the operator boundary. It also makes
future RAG or GraphRAG preparation possible through compact anchors without
turning generated navigation into retrieval authority, memory truth, proof, or
owner acceptance.

## Consequences

- Old `current/` checkpoint pressure becomes inspectable without moving files.
- Runtime trace gaps become explicit instead of collapsing into stale scope.
- Session-memory archive absence remains weaker than archive proof.
- Pending review remains a hard required action.
- Future timers, if any, can wrap explicit dry-run commands instead of hiding
  closeout, review, harvest, memory mutation, or owner movement.

## Source Surfaces

- `src/aoa_sdk/checkpoints/backlog.py`
- `src/aoa_sdk/checkpoints/backlog_indexes.py`
- `src/aoa_sdk/checkpoints/lifecycle.py`
- `src/aoa_sdk/checkpoints/session_memory.py`
- `src/aoa_sdk/checkpoints/indexes.py`
- `src/aoa_sdk/contracts/checkpoints.py`
- `src/aoa_sdk/cli/checkpoint.py`
- `src/aoa_sdk/cli/rendering.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/`
- `mechanics/checkpoint/README.md`
- `mechanics/checkpoint/ROADMAP.md`

## Follow-Up Route

Use `backlog-audit` before applying no-closeout cleanup. Route runtime trace
gaps to aoa-session-memory freshness, sweep, import, or recovery checks; route
reconcile-ready scopes to `reconcile-sessions --dry-run`; route pending scopes
to checkpoint review.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
