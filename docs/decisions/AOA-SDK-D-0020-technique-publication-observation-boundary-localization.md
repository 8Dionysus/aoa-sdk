# Technique Publication Observation Boundary Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0020
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, active naming
- SDK facets: mechanics topology, recurrence, hook observation
- Mechanic parents: recurrence
- Guard families: mechanics topology, docs routes, active naming, owner boundary
- Posture: accepted

## Context

After the Codex workspace MCP server slice, the root docs district still held
`docs/TECHNIQUE_PUBLICATION_HOOKS.md`. The file is not a Techniques source
facade and not a new parent mechanic. It defines when technique-sensitive hooks
may emit observations without turning techniques into auto-activated skills or
auto-canonicalized runtime artifacts.

That route belongs to the Recurrence hook observation pack: input is a
technique-sensitive publication, evidence, or review moment; output is an
observation signal; owner truth remains in `aoa-techniques`.

## Decision

Move the root note into:

- `mechanics/recurrence/parts/hook-observation-pack/docs/technique-publication-observation-boundary.md`

Name the active surface as an observation boundary, not as generic technique
hooks.

## Rationale

The old title was easy to misread as SDK-owned runtime hooks for techniques.
The part-local name shows the operational map: recurrence hook observation reads
reviewable moments, emits bounded signals, and routes onward to beacon pressure
and owner review. It does not authorize promotion, canonical status, or runtime
execution.

## Consequences

- Root `docs/` no longer carries the active technique-hook guidance payload.
- Recurrence hook docs now name the technique publication boundary as an
  observation-only stop-line.
- `aoa-techniques` keeps technique canon, distillation, review, and promotion
  authority.

## Source Surfaces

- `mechanics/recurrence/parts/hook-observation-pack/`
- `mechanics/recurrence/parts/hook-observation-pack/docs/technique-publication-observation-boundary.md`
- `mechanics/recurrence/README.md`
- `mechanics/recurrence/PARTS.md`
- `mechanics/recurrence/PROVENANCE.md`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `README.md`

## Follow-Up Route

Continue root technical district audit for Checkpoint test placement, Questbook
payload, and remaining cross-mechanic public contracts.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
