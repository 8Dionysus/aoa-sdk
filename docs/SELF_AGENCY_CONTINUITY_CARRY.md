# Self-Agency Continuity Carry

`aoa-sdk` may carry reviewed-closeout continuity hints when a route needs
bounded self-agency continuity across more than one revision window.
It does not define self-agency meaning.

## Boundary

- `aoa-sdk` may carry continuity hints only after a reviewed anchor already
  exists
- the SDK may name `continuity_ref_hint`, `revision_window_ref_hint`,
  `anchor_artifact_ref`, `reanchor_need`, and `continuity_status_hint`
- the SDK may point back to the inspected closeout artifact that would survive
  a return
- the SDK does not mint reviewed continuity truth
- the SDK does not mint self-agent authority
- the SDK does not let memo, stats, or playbook projections become continuity
  truth

## Carried shape

The compact carry chain is:

`continuity_ref_hint -> revision_window_ref_hint -> anchor_artifact_ref`

`reanchor_need` and `continuity_status_hint` stay advisory fields around that
chain.

The public example lives in
`examples/closeout_continuity_window.example.json` and validates against
`schemas/closeout_continuity_window.schema.json`.

## Carry rules

- `continuity_ref_hint` names the reviewed continuity thread the SDK thinks the
  route may now belong to
- `revision_window_ref_hint` names the bounded revision window rather than the
  whole session history
- `anchor_artifact_ref` must point to an inspectable artifact, not to vague
  chat continuity
- `reanchor_need` stays a control-plane warning flag
- `continuity_status_hint` stays within `active`, `reanchor_needed`,
  `reanchored`, or `closed`

## Negative rules

- do not turn this carry into runtime self-modification authority
- do not let the SDK decide whether a route truly earned self-agency
- do not let the hint outrank `aoa-agents`, `aoa-playbooks`, `aoa-memo`, or
  `aoa-evals`
- do not point reanchor at remembered context when a named artifact is missing
