# AGENTS.md

## Applies to

`mechanics/skill-routing/`.

## Role

Route the SDK-local skill-routing mechanic for portable skill detection,
disclosure, activation, guard, dispatch, and runtime session surfaces.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/skill-routing/README.md`
- `.agents/skills/`
- `docs/skill-runtime-recommendation-gap.md`
- `src/aoa_sdk/skills/`

## Boundaries

- Stay on the control plane.
- Keep `aoa skills ...` skill-only.
- Do not make SDK skill routing the canon for skill meaning.
- Keep explicit-only skills in visible confirmation lanes.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_skills.py tests/test_skill_reference_contracts.py
```

## Closeout

Report whether detection, disclosure, activation, dispatch, or session storage
changed.
