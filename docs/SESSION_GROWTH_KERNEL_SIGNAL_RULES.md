# Session Growth Kernel Signal Rules

`aoa-sdk` may publish one reviewed-only `followthrough_decision` during
checkpoint closeout.

This surface stays on the control plane.
It names one honest next kernel class after the reviewed reread.
It does not execute that class, and it does not replace owner truth.

## Boundary

- the decision is emitted only from reviewed closeout context
- it is a sibling to `candidate_lineage_map` and `owner_followthrough_map`
- it remains advisory and does not auto-run from `aoa closeout run`
- `aoa-session-donor-harvest` remains part of the explicit closeout bridge,
  but it is not the output of this decision surface
- `candidate_ref` may appear only as foreign carry; `aoa-sdk` does not mint it
- `seed_ref` and `object_ref` remain forbidden

## Decision question

Use this surface when the reviewed reread needs to answer:

- which next kernel skill best matches the current reviewed route

without pretending the skill already ran.

## Deterministic rule ladder

The current rule ladder is intentionally narrow:

1. recurring playbook-shaped route evidence with stable output shape ->
   `aoa-automation-opportunity-scan`
2. explicit repair-shaped evidence ->
   `aoa-session-self-repair`
3. repeated friction, blockers, or thin-evidence posture ->
   `aoa-session-self-diagnose`
4. explicit axis movement with no repair need ->
   `aoa-session-progression-lift`
5. repeated reviewed promotion pressure ->
   `aoa-quest-harvest`
6. otherwise, when several plausible lanes remain ->
   `aoa-session-route-forks`

The rule ladder stays deterministic and reviewable.
It is not a hidden recommender model.

## Reason codes

The decision may currently use these reason codes:

- `multiple_plausible_next_moves`
- `repeated_friction`
- `blocked_automation_readiness`
- `reviewed_diagnosis_present`
- `smallest_repair_clear`
- `explicit_axis_movement`
- `no_repair_needed`
- `repeated_manual_route`
- `stable_output_shape`
- `checkpoint_sensitive`
- `reviewed_quest_unit`
- `promotion_pressure`

Reason codes explain why the decision was chosen.
They do not upgrade the decision into proof or approval.

## Reading rule

Read `followthrough_decision` together with:

- `docs/CANDIDATE_LINEAGE_CARRY.md`
- `docs/closeout-followthrough-map.md`
- `docs/session-growth-checkpoints.md`

For component-refresh drift routing rather than next-kernel skill selection,
read `docs/COMPONENT_DRIFT_HINTS.md`.

If the question is already about execution, owner truth, approval, or
publisher output, leave this surface and read the owning repository instead.
