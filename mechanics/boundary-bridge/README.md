# Boundary Bridge Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Keep SDK typed facades as handles over source-owned sibling surfaces while the
sibling repositories retain meaning.

### Trigger

Use this mechanic when a typed facade, registry, route hint, stats read, or
sibling-owned generated reader changes.

### SDK owns

- typed loading and facade shape
- local truth labels
- source references and route hints
- owner return path after stronger claims appear

### Stronger owner split

`aoa-routing`, `aoa-skills`, `aoa-evals`, `aoa-memo`, `aoa-agents`,
`aoa-playbooks`, `aoa-techniques`, stats/KAG owners, and other sibling repos
retain their domain meaning.

### Current source surfaces

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
- facade tests under `tests/`

### Candidate parts

- typed-facades
- truth-labels
- owner-return-routes

### Must not claim

This mechanic must not turn loaded sibling catalogs into SDK source truth or
change sibling semantics by changing a Python facade.

### Validation

```bash
python -m pytest -q tests/test_agents.py tests/test_evals.py tests/test_memo.py tests/test_routing.py
```

### Next route

For new sibling-owned meaning, update the owning sibling repo first, then the
SDK facade and compatibility path.
