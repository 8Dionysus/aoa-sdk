# Compatibility Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Check consumed sibling surface paths, stable SDK surface IDs, sibling canary
expectations, and release/version posture without hidden fallback.

### Trigger

Use this mechanic when a sibling surface moves, a compatibility rule changes, a
canary matrix entry changes, or an SDK release claim depends on consumed
sibling topology.

### SDK owns

- stable SDK-level surface identifiers
- compatibility policy for surfaces the SDK consumes
- canary checks over local sibling workspaces
- versioning posture for public SDK support

### Stronger owner split

Sibling repositories own physical topology and source meaning. The SDK follows
their canonical owner-local paths instead of creating alternate truth.

### Current source surfaces

- `docs/versioning.md`
- `docs/boundaries.md`
- `scripts/run_sibling_canary.py`
- `scripts/sibling_canary_matrix.json`
- `src/aoa_sdk/compatibility/`
- `tests/test_compatibility.py`
- `tests/test_sibling_canary.py`

### Candidate parts

- canonical-path-policy
- sibling-canary
- version-posture

### Must not claim

This mechanic must not make legacy paths supported fallback or hide topology
drift behind permissive compatibility.

### Validation

```bash
aoa compatibility check /srv/AbyssOS/aoa-sdk
aoa compatibility check /srv/AbyssOS/aoa-sdk --repo aoa-skills --json
python -m pytest -q tests/test_compatibility.py tests/test_sibling_canary.py
```

### Next route

When a sibling topology changes, update `src/aoa_sdk/compatibility/policy.py`,
tests, and a decision record if future agents need the route rationale.
