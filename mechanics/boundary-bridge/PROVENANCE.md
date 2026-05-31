# Boundary Bridge Provenance

## Source Surfaces

- `docs/boundaries.md`
- `src/aoa_sdk/agents/`
- `src/aoa_sdk/evals/`
- `src/aoa_sdk/governed_runs/`
- `src/aoa_sdk/kag/`
- `src/aoa_sdk/memo/`
- `src/aoa_sdk/playbooks/`
- `src/aoa_sdk/routing/`
- `src/aoa_sdk/stats/`
- `src/aoa_sdk/techniques/`
- `tests/test_agents.py`
- `tests/test_evals.py`
- `tests/test_memo.py`
- `tests/test_routing.py`

## Stronger Owners

Sibling repositories own their domain semantics. The SDK owns typed access,
validation, and handoff readability.

## Notes

This shared mechanic name matches the repeated AoA boundary pattern: bridge the
surface, keep ownership outside.
