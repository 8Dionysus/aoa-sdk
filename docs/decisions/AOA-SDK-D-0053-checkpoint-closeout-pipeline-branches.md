# Checkpoint Closeout Pipeline Branches

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0053
- Original date: 2026-06-03
- Surface classes: source-topology, checkpoint, implementation, validation
- SDK facets: importable implementation, checkpoint control-plane, closeout bridge
- Mechanic parents: checkpoint
- Guard families: source topology, checkpoint route roles, closeout boundary
- Posture: accepted

## Context

`src/aoa_sdk/checkpoints/closeout/bridge.py` became the remaining
medium-pressure checkpoint branch after the route-role split in
`AOA-SDK-D-0052`.

The module had the right topological owner, but it still mixed distinct
closeout pipeline responsibilities: followthrough decision posture, session
scope and receipt loading, reviewed artifact and Codex trace evidence reads,
mechanical artifact and receipt construction, and owner follow-through handoff
assembly.

Leaving those families in one bridge would keep future agents entering a broad
helper surface before they could find the owner of a closeout behavior.

## Options Considered

- Leave `closeout/bridge.py` as the single reviewed closeout helper module.
- Split by artifact name or output filename.
- Split the public `CheckpointsAPI` closeout methods.
- Keep public API orchestration stable and split closeout internals by pipeline
  role.

## Decision

Keep `CheckpointsAPI.build_closeout_context` and
`CheckpointsAPI.execute_closeout_chain` as the public closeout entrypoints.

Split checkpoint closeout internals into route-role branches:

- `closeout/followthrough.py` owns lineage followthrough decisions and
  next-skill posture.
- `closeout/context.py` owns closeout scope, surface handoff loading, receipt
  input loading, session-ref resolution, candidate maps, and skill-plan hints.
- `closeout/evidence.py` owns reviewed artifact reads, Codex session trace
  extraction, and evidence merging.
- `closeout/execution.py` owns mechanical donor-harvest, progression-lift, and
  quest-harvest packet and receipt builders.
- `closeout/owner_handoff.py` owns owner follow-through handoff writing,
  accepted candidate shaping, owner routing, and quest promotion fields.
- `closeout/contracts.py` and `closeout/common.py` own small shared contracts
  and helpers needed to avoid circular imports.
- `closeout/bridge.py` remains a thin compatibility facade over the pipeline
  branches.

## Rationale

The split follows the checkpoint mechanic boundary. Checkpoint closeout may
build mechanical context, packets, receipts, and handoffs, but it must not
become durable memory, final proof, progression truth, quest acceptance, or
owner approval.

Pipeline names tell an agent which branch owns a behavior before reading the
whole closeout implementation. The generated topology remains a read model and
does not replace source files, tests, route cards, or this rationale.

## Consequences

- `closeout/bridge.py` is no longer the closeout implementation sink.
- New closeout behavior should land in the branch that owns its pipeline role.
- Mechanical artifact payload shapes and CLI/API behavior remain governed by
  checkpoint part tests and `CheckpointsAPI`.
- `registry.py` remains the public facade and should not absorb closeout helper
  families back into itself.
- `ledger/notes.py` remains a coherent checkpoint ledger branch unless a future
  change proves a separate owner boundary for note assembly, runtime loading,
  or progression-axis derivation.

## Source Surfaces

- `src/aoa_sdk/checkpoints/closeout/bridge.py`
- `src/aoa_sdk/checkpoints/closeout/context.py`
- `src/aoa_sdk/checkpoints/closeout/evidence.py`
- `src/aoa_sdk/checkpoints/closeout/execution.py`
- `src/aoa_sdk/checkpoints/closeout/followthrough.py`
- `src/aoa_sdk/checkpoints/closeout/owner_handoff.py`
- `src/aoa_sdk/checkpoints/closeout/contracts.py`
- `src/aoa_sdk/checkpoints/closeout/common.py`
- `src/aoa_sdk/checkpoints/registry.py`
- `src/aoa_sdk/checkpoints/ledger/notes.py`
- `generated/source_topology.min.json`
- `tests/test_source_topology_index.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/`

## Follow-Up Route

Keep the next checkpoint cut outside closeout unless a new closeout behavior
adds real pressure to one pipeline branch. The next broad SDK split-pressure is
more likely to live in shared models, CLI command assembly, or another
implementation family, not in the closeout facade.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
