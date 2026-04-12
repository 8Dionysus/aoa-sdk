# Closeout Followthrough Map

`aoa-sdk` may publish one reviewed-only closeout followthrough map beside the
existing candidate lineage carry.

This map stays on the control plane.
It points toward the first owner-status surface and the next decision class.
It does not claim that owner landing already happened.

## Boundary

Keep these closeout contexts separate:

- `candidate_lineage_map` says which lineage hints survived the reviewed
  reread
- `owner_followthrough_map` says which owner-status surface should receive the
  next honest tracked move
- owner repositories still decide whether the route lands, reanchors, stages a
  seed, merges, defers, or drops

## Allowed Carry

The followthrough map may carry:

- `cluster_ref`
- optional `candidate_slot`
- `owner_hypothesis`
- `owner_shape`
- `nearest_wrong_target`
- `status_posture`
- `recommended_owner_status_surface`
- `requested_next_decision_class`
- `evidence_refs`

## Forbidden Carry

The followthrough map must not carry `candidate_ref`, `seed_ref`, or
`object_ref`.

More explicitly, it must not carry:

- `candidate_ref`
- `seed_ref`
- `object_ref`

That keeps `aoa-sdk` from turning reviewed closeout into owner identity minting.

## Relationship To Closeout

`aoa checkpoint build-closeout-context` may write both maps into
`closeout-context.json`:

- lineage carry remains provisional
- followthrough remains advisory
- final owner truth still belongs to reviewed owner status surfaces, seed
  staging, proof, and landed objects in their owning repositories

## Reading Rule

Use this map when reviewed closeout needs to say where the next tracked move
belongs without pretending that the move already ran.

If the question is already about final owner truth, leave `aoa-sdk` and read
the owner repository instead.
