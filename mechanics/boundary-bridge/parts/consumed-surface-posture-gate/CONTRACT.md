# Consumed Surface Posture Gate Contract

## Guarantees

- Reads consumed surfaces only through explicit compatibility rules or typed
  facade methods.
- Preserves source-owner authority in reports and model fields.
- Requires canonical refactored sibling paths when a sibling repo has already
  moved the surface into mechanics; old root generated copies are not active
  compatibility inputs.
- Rejects routing action surfaces that do not have an explicit compatibility
  rule.
- Keeps a succession baseline explicitly weaker than the current source owner
  until a durable owner-succession decision and canonical switch are landed.
- Keeps accepted target ownership distinct from current producer authority,
  requires the paired repository decisions before G5, and preserves routing
  ABI paths during the owner-only switch.
- Names one authority owner for each discover, candidate, authorization,
  activation, execution, evaluation, retention, and closeout operation.

## Non-Goals

- It does not define sibling surface meaning.
- It does not promote loaded data into SDK-owned truth.
- It surfaces incompatible, malformed, or missing owner paths as compatibility
  failures.
- A dependency or disposition audit is not an authority transfer.
- A target operating model is not a producer switch, runtime trust admission,
  or archive authorization.

## Active Test Home

- `tests/test_consumed_surface_compatibility_gate.py`
- `tests/test_agent_phase_binding_surface_reader.py`
- `tests/test_eval_surface_reader.py`
- `tests/test_governed_run_surface_reader.py`
- `tests/test_kag_surface_reader.py`
- `tests/test_memo_surface_reader.py`
- `tests/test_playbook_surface_reader.py`
- `tests/test_routing_surface_actions.py`
- `tests/test_stats_surface_reader.py`
- `tests/test_workspace_control_plane_compatibility.py`
- `tests/test_routing_succession_r0_baseline.py`
- `tests/test_routing_succession_r1_target_operating_model.py`
