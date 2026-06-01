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

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/experience/parts/capture-pipeline-helper/tests/test_capture_pipeline_helper.py mechanics/agon/parts/center-law-preview-helpers/tests/test_agon_ccs_sdk_helper_candidates.py mechanics/agon/parts/state-packet-review-bindings/tests/test_agon_sdk_state_packet_bindings.py mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_duel_kernel_sdk_bindings.py mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_mechanical_trial_sdk_helpers.py mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_vds_sdk_helper_candidates.py mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_retention_rank_sdk_helpers.py mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_epistemic_sdk_helpers.py mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_kag_sdk_helpers.py mechanics/agon/parts/school-lineage-campaign-review-helpers/tests/test_agon_slc_sdk_helpers.py mechanics/agon/parts/sophian-threshold-review-helpers/tests/test_agon_sophian_sdk_helpers.py
```
