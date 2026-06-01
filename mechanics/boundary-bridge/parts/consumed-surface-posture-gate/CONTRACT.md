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

## Non-Goals

- It does not define sibling surface meaning.
- It does not promote loaded data into SDK-owned truth.
- It surfaces incompatible, malformed, or missing owner paths as compatibility
  failures.

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
