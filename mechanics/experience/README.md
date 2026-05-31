# Experience Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Maintain Experience API helper contracts for adoption, deployment, governance,
watchtower, rollback, release, dashboard, and related SDK call surfaces.

### Trigger

Use this mechanic when an Experience API doc, SDK call schema, example, or seed
contract test changes.

### SDK owns

- typed call contract schemas
- public-safe examples
- seed contract regression tests
- documentation of the SDK helper boundary

### Stronger owner split

Experience owners retain operational decisions, adoption authority, deployment
truth, governance truth, watchtower meaning, rollback authority, and release
acceptance.

### Current source surfaces

- `docs/EXPERIENCE_ADOPTION_API.md`
- `docs/EXPERIENCE_DEPLOYMENT_API.md`
- `examples/sdk_adoption_request_call.example.json`
- `schemas/sdk_adoption_request_call_v1.json`
- `tests/test_experience_wave2_seed_contracts.py`
- `tests/test_experience_wave3_seed_contracts.py`
- `tests/test_experience_wave4_seed_contracts.py`
- `tests/test_experience_wave5_seed_contracts.py`

### Candidate parts

- adoption
- deployment
- governance
- watchtower
- rollback
- release

### Must not claim

This mechanic must not turn a valid SDK helper call into approval to execute an
Experience operation.

### Validation

```bash
python -m pytest -q tests/test_experience_wave2_seed_contracts.py tests/test_experience_wave3_seed_contracts.py tests/test_experience_wave4_seed_contracts.py tests/test_experience_wave5_seed_contracts.py
```

### Next route

Operational meaning routes to the Experience owner; SDK changes stay in
schemas, examples, docs, and tests.
