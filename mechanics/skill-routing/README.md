# Skill Routing Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Detect, disclose, activate, guard, and dispatch portable skills while keeping
skill canon and activation meaning in `aoa-skills`.

### Trigger

Use this mechanic when `.agents/skills` exports, `aoa skills ...` CLI behavior,
phase-aware detection, or runtime skill session storage changes.

### SDK owns

- portable skill export discovery
- disclosure and activation helper behavior
- phase-aware detector and guard output
- local runtime session storage for SDK wrappers

### Stronger owner split

`aoa-skills` owns skill canon, skill execution meaning, and preferred versus
explicit-only policy.

### Current source surfaces

- `.agents/skills/`
- `docs/skill-runtime-recommendation-gap.md`
- `docs/skill-runtime-recommendation-gap-fix-spec.md`
- `src/aoa_sdk/skills/`
- `tests/test_skills.py`
- `tests/test_skill_reference_contracts.py`

### Candidate parts

- discovery
- disclosure
- activation
- phase-dispatch
- runtime-session

### Must not claim

This mechanic must not make `aoa skills detect/dispatch/enter/guard` activate
non-skill surfaces or silently apply explicit-only skills.

### Validation

```bash
python -m pytest -q tests/test_skills.py tests/test_skill_reference_contracts.py
```

### Next route

Skill meaning changes route to `aoa-skills`; SDK wrapper behavior changes stay
with `src/aoa_sdk/skills/`, CLI tests, and this mechanic.
