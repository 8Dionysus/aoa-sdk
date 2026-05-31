# AGENTS.md

## Applies to

`mechanics/boundary-bridge/`.

## Role

Route the shared boundary-bridge mechanic for typed SDK facades that keep SDK
handles separate from sibling-owned meaning.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/boundary-bridge/README.md`
- `docs/boundaries.md`
- `src/aoa_sdk/*/registry.py`
- `src/aoa_sdk/routing/`

## Boundaries

- Stay on the control plane.
- Do not make a facade a source owner.
- Preserve truth labels and owner return routes.
- Keep sibling policy, proof, memory, role, and routing meaning outside SDK
  source truth.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_agents.py tests/test_evals.py tests/test_memo.py tests/test_routing.py
```

## Closeout

Report which facade changed and which sibling owner still owns meaning.
