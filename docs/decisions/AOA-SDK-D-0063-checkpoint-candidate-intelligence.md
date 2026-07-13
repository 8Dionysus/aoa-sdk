# Checkpoint Candidate Intelligence Navigation

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0063
- Original date: 2026-06-04
- Surface classes: checkpoint, classifier, generated-index, wrapper-gap, validation
- SDK facets: checkpoint control-plane, candidate intelligence, CLI facade, surface detection
- Mechanic parents: checkpoint
- Guard families: no single-event promotion, generated navigation, review gate, owner boundary
- Posture: accepted

## Context

Checkpoint candidate capture already preserved `candidate_kind`, `owner_hint`,
`source_surface_ref`, lineage hints, and progression-axis pressure. That was
useful as a compatibility layer, but too flat for the next question: when does
a repeated action deserve a candidate wrapper such as a skill, playbook,
technique, eval, memo route, SDK-local checkpoint mechanic, or owner-local
wrapper?

The flat route also biased classification toward existing aoa-* surfaces. A
missing wrapper or unfamiliar repeated action could be forced into the nearest
known surface instead of being preserved as a wrapper gap.

## Decision

Add checkpoint candidate intelligence as a deterministic wrapper-navigation
layer below legacy `candidate_kind`.

The chain is:

```text
action event facets -> action signature -> repetition cluster -> wrapper gap
candidate -> owner/review lane
```

The SDK records `CheckpointActionEvent`, `ActionSignature`,
`RepetitionCluster`, `ExistingWrapperFit`, `WrapperReadiness`,
`WrapperGapCandidate`, and bounded sample-audit contracts. The classifier
distinguishes wrapper lanes for skill, playbook, technique, eval, memo,
SDK-local checkpoint mechanic, owner-local, and unknown/gap pressure.

This decision does not define the ecosystem carrier ontology for mechanics,
tools, MCP services, hooks, scripts, daemons, services, or indexes. That
corrective carrier axis is handled by AOA-SDK-D-0064.

`candidate_clusters` remain the compatibility surface. Their
`action_signature_refs` point into the richer classifier evidence, but the
old fields stay readable for existing checkpoint closeout and promotion gates.
Legacy saved `ActionSignature` records may lack the newer classifier axes. The
report route re-enriches those signatures from action events and saved event
refs, then normalizes single-event negative evidence against the recovered
repeat count. This is generated navigation; it does not rewrite the checkpoint
note or promote the signature.

`aoa checkpoint candidate-intelligence` can report the current note and, with
`--write-index`, writes
`.aoa/session-growth/indexes/checkpoint-candidate-intelligence.min.json`.
That index groups signatures, repetition clusters, wrapper gaps, owner
pressure, existing-fit status, sample-audit targets, and graph-ready anchors.

## Rationale

aoa-session-memory showed the right meta-form: generated indexes route raw
evidence, but they are not reviewed memory. Its event typing also shows why a
single flat `event_type` is not enough; classification needs family, phase,
actor, action, object, outcome, route signals, relationships, and review
feedback space.

The SDK owns checkpoint control-plane visibility. It can expose classifier
route evidence, but it must not accept a wrapper, create durable memory, prove
an invariant, assign owner truth, or promote a candidate from one event.

## Consequences

- Repeated checkpoint actions can be inspected by action signature instead of
  only by legacy candidate kind.
- Novel pressure can remain `unknown` / wrapper-gap evidence instead of being
  flattened into the nearest existing aoa-* owner.
- Single-event weak evidence remains observe-only; repeated evidence can
  become reviewable, and higher draftability still stays a review signal.
- Generated graph-ready anchors prepare for RAG/GraphRAG-style navigation
  without making the SDK a retrieval or memory owner.

## Source Surfaces

- `src/aoa_sdk/checkpoints/candidate_intelligence.py`
- `src/aoa_sdk/checkpoints/candidate_indexes.py`
- `src/aoa_sdk/checkpoints/ledger/notes.py`
- `src/aoa_sdk/checkpoints/registry.py`
- `src/aoa_sdk/contracts/checkpoints.py`
- `src/aoa_sdk/contracts/surfaces.py`
- `src/aoa_sdk/surfaces/registry.py`
- `src/aoa_sdk/cli/checkpoint.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/`

## Follow-Up Route

Use sample-audit verdicts to accept, reject, weaken, split, or add classifier
rules. Do not auto-draft skills, playbooks, techniques, evals, memo entries,
SDK-local checkpoint mechanics, or owner-local wrappers from the generated
index.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
