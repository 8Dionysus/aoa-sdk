# Agon and Experience Part Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0009
- Original date: 2026-05-31
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, artifact localization, Agon helpers, Experience helpers, root technical districts
- Mechanic parents: agon, experience, questbook
- Guard families: mechanics topology, part validation, schema validation, generated registry parity
- Posture: accepted

## Context

After the first Agon recurrence-adapter localization, root technical districts
still carried most Agon helper payload: seeds, docs, schemas, examples,
generated registries, quests, builders, validators, and tests.

Those payloads were not repo-wide root contracts. They were SDK-owned helper
routes for existing shared mechanics. Keeping them in root made the active
surface flat: an agent could see `docs/AGON_*` and `config/agon_*` but not the
owner route, output, validation home, or stronger-owner boundary.

One root file also had misleading pressure: `AGON_WAVE1_EXPERIENCE_CAPTURE_PIPELINE`
looked Agon-owned by filename, but its actual operation is the Experience
capture/pipeline helper seam.

## Decision

Localize Agon helper payload into functioning `mechanics/agon/parts/` homes:

- `center-law-preview-helpers`
- `state-packet-review-bindings`
- `recurrence-adapter`
- `duel-kernel-review-bindings`
- `verdict-retention-rank-review-helpers`
- `epistemic-kag-review-helpers`
- `school-lineage-campaign-review-helpers`
- `sophian-threshold-review-helpers`

Localize the Wave I Experience capture/pipeline helper seam into
`mechanics/experience/parts/capture-pipeline-helper/`.

Agon helper contracts move with their owning helper part. `AOA-SDK-D-0042`
restores durable quest source records to root `quests/<lane>/<state>/` and
keeps Questbook responsible for source-store follow-through semantics.

## Rationale

The active topology should expose the operation map directly: role, input,
output, owner, next route, validation, and stop-line. Part names therefore
name the route pressure rather than the old root district or wave note.

This keeps `agon` and `experience` as shared parent mechanics instead of
creating SDK-local parent mechanics for each helper family. It also prevents
`Experience capture` from remaining under Agon just because an old file name
started with `AGON_`.

## Consequences

- Root `config/`, `docs/`, `schemas/`, `examples`, `generated/`, `quests/`,
  `scripts/`, and `tests/` no longer own these single-mechanic helper payloads.
- Former root paths are provenance and migration receipts only.
- Each localized part owns a `README.md`, `CONTRACT.md`, `VALIDATION.md`, and
  local artifact districts.
- Existing registry IDs and helper ids remain stable unless a separate
  compatibility decision changes them.

## Source Surfaces

- `mechanics/agon/PARTS.md`
- `mechanics/agon/PROVENANCE.md`
- `mechanics/agon/parts/`
- `mechanics/experience/PARTS.md`
- `mechanics/experience/PROVENANCE.md`
- `mechanics/experience/parts/capture-pipeline-helper/`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `mechanics/questbook/PARTS.md`

## Follow-Up Route

Continue the root technical district audit for remaining single-mechanic-owned
payload outside Agon, Experience, and Codex Projection.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
