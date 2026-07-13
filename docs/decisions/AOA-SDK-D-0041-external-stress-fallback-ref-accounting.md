# External Stress Fallback Ref Accounting

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0041
- Original date: 2026-06-01
- Surface classes: active naming, external source ref, compatibility accounting, stress evidence
- SDK facets: antifragility stress posture, reviewed stress carry, active naming, owner boundary
- Mechanic parents: antifragility
- Guard families: active naming, source ref preservation, owner boundary, part validation
- Posture: accepted

## Context

Antifragility stress examples preserve real evidence handles from source-owned
or routing-owned surfaces. Some of those handles contain `fallback`, for
example `retrieval-only-fallback`.

The SDK does not own those external handles. Renaming them inside `aoa-sdk`
would make the examples easier to grep but weaker as evidence, because the
refs would no longer match sibling source and routing surfaces.

## Decision

Keep source-owned and routing-owned stress refs exact in part-local examples.

Document them as external evidence handles in the Stress Posture Dispatch Gate
and Reviewed Stress Closeout Carry contracts. They are not SDK-owned active
route names.

New SDK-owned stress posture fields, examples, and routes must use explicit
degraded, recovery, source-first, or alternate-path vocabulary instead of
introducing fallback-shaped active names.

## Rationale

The goal is not to erase source evidence. The goal is to keep active SDK
surface naming honest.

External refs identify the owner evidence that an agent should inspect next.
SDK-owned names identify the route the SDK owns. Preserving that split keeps
the operating map legible without falsifying provenance.

## Consequences

- `retrieval-only-fallback` may appear only as an external source/routing
  evidence handle in Antifragility examples.
- Contracts state that those strings are not SDK-owned active route names.
- Part tests prove the accounting text stays present.

## Source Surfaces

- `mechanics/antifragility/parts/stress-posture-dispatch-gate/CONTRACT.md`
- `mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/`
- `mechanics/antifragility/parts/reviewed-stress-closeout-carry/CONTRACT.md`
- `mechanics/antifragility/parts/reviewed-stress-closeout-carry/examples/`

## Follow-Up Route

If source owners rename the stress refs, update the examples to match owner
truth. Do not mint SDK-owned fallback route names to smooth over the change.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
