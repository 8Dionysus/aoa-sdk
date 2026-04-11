# Candidate Lineage Carry

`aoa-sdk` carries provisional checkpoint and closeout lineage hints for growth
refinery without claiming owner truth.

## Boundary

- `aoa-sdk` may mint and carry `cluster_ref`
- `aoa-sdk` may carry `owner_hypothesis`, `owner_shape`,
  `nearest_wrong_target`, `evidence_refs`, `axis_pressure`,
  `status_posture`, `supersedes`, `merged_into`, and `drop_reason`
- `aoa-sdk` does not mint `candidate_ref`
- `aoa-sdk` does not mint `seed_ref`
- `aoa-sdk` does not mint `object_ref`
- checkpoint and closeout lineage stays provisional until reviewed owner-layer
  harvest, seed staging, and final owner landing resolve the next identifiers

## Carried shape

The control-plane carry uses `schemas/checkpoint_lineage_hint.schema.json` and
lands in two places:

- checkpoint candidate clusters under `lineage_hint`
- reviewed closeout context under `candidate_lineage_map`

The canonical growth-refinery axis remains:

`cluster_ref -> candidate_ref -> seed_ref -> object_ref`

In this repo only the first hop is authoritative.

## Carry rules

- `cluster_ref` must be deterministic for the checkpoint candidate seam
- `owner_hypothesis` stays a hypothesis, not a final owner verdict
- `owner_shape` names the expected owner-side surface shape, not a landed
  object
- `nearest_wrong_target` keeps the most tempting adjacent owner mistake visible
- `status_posture` stays within `early`, `reanchor`, `thin-evidence`, or
  `stable`
- `axis_pressure` is a compact checkpoint-to-closeout carry, not a score
- `supersedes`, `merged_into`, and `drop_reason` stay representable even before
  owner truth exists

## Negative rules

- do not turn checkpoint lineage carry into donor-harvest authority
- do not upgrade a checkpoint hint into a seed or owner object from `aoa-sdk`
- do not let closeout packets pretend the owner repo already accepted the unit
