# Component Drift Hints

`aoa-sdk` may carry component-refresh signals on the control plane without
becoming the owner of the drifting component.

## Purpose

Use this note when repeated drift, stale generated surfaces, repeated hand
patches, doctor failures, or stale summary windows point at one internal
component that already has an owner repository.

This carry exists so reviewed closeout can preserve the next bounded refresh
move without pretending the refresh already ran.

## Boundary

`aoa-sdk` may carry:

- `component_drift_hint` during checkpoint or reviewed-closeout reread
- reviewed `component_refresh_followthrough_decision` after the reread
- owner repo, route class, evidence refs, rollback anchors, and refresh
  freshness posture

`aoa-sdk` must not:

- regenerate owner surfaces by itself
- treat a hint as a completed owner refresh receipt
- claim that owner validation already passed
- turn component refresh into a hidden scheduler lane

## Control-plane surfaces

The control-plane contract uses:

- `schemas/component_drift_hint_set.schema.json`
- `examples/component_drift_hints.example.json`
- `schemas/component_refresh_followthrough_decision_set.schema.json`
- `examples/component_refresh_followthrough_decision.example.json`

Wave alpha keeps both surfaces weaker than owner refresh laws and owner
receipts. They are carry contracts, not proof that the owner repo refreshed the
component.

## Carried shape

`component_drift_hint` may carry:

- `hint_ref`
- `component_ref`
- `owner_repo`
- `observed_at`
- `observed_by`
- `severity`
- `signals`
- `repeat_count`
- `evidence_refs`
- `recommended_route_class`
- `review_required`

`component_refresh_followthrough_decision` may carry:

- `component_ref`
- `owner_repo`
- `route_class`
- `decision_status`
- `selected_refresh_path`
- `reason`
- `evidence_refs`
- `rollback_anchor`
- `stats_should_refresh`
- `memo_writeback_candidate`

## Reading rule

Use these surfaces when reviewed closeout needs to preserve:

- which component appears to be drifting
- which owner repo should handle the refresh
- which bounded refresh route is the next honest move

If the question is already about the owner refresh law, validation result, or
rollback truth, leave `aoa-sdk` and read the owner repository instead.

## Relationship to closeout

These surfaces may sit beside:

- checkpoint-note carry under `.aoa/session-growth/current/.../`
- `candidate_lineage_map`
- `owner_followthrough_map`
- `followthrough_decision`

They remain companion carry, not replacement authority.

Wave alpha does not auto-emit these packets from `aoa surfaces handoff` or
`aoa checkpoint build-closeout-context`.
They exist so reviewed wrappers and owner repos can share one explicit control
plane vocabulary before any stronger automation wave is considered.
