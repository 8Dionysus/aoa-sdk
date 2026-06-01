# AGENTS.md

## Applies To

This card applies to `sdk/public-interface/`.

## Role

`sdk/public-interface/` names the public SDK contract posture for Python API,
CLI, and typed model surfaces.

It routes consumer-facing promises to implementation and tests without making
this source-home branch stronger than `src/aoa_sdk/`.

## Read Before Editing

1. root `AGENTS.md`
2. `sdk/AGENTS.md`
3. `sdk/source_home.manifest.json`
4. `sdk/public-interface/README.md`
5. the target family README
6. the named implementation and mechanic route

## Boundaries

- Keep executable behavior in `src/aoa_sdk/`.
- Keep repeatable operation pressure in `mechanics/`.
- Keep public API posture tied to tests.
- Do not document a supported entrypoint that is not implemented.
- Do not turn typed models into sibling-source authority.

## Validation

```bash
python scripts/validate_sdk_source_home.py
python -m pytest -q tests/test_sdk_source_home.py
python -m pytest -q
```

## Closeout

State whether the change touched Python API posture, CLI posture, model
posture, implementation, or mechanic routes.
