# AGENTS.md

## Applies To

This card applies to `sdk/facade-boundary/`.

## Role

`sdk/facade-boundary/` names how SDK facades read sibling-owned surfaces while
keeping sibling meaning outside the SDK.

It routes sibling-reader, compatibility, and truth-label pressure to the
implementation and Boundary Bridge mechanics.

## Read Before Editing

1. root `AGENTS.md`
2. `sdk/AGENTS.md`
3. `sdk/source_home.manifest.json`
4. `sdk/facade-boundary/README.md`
5. the target family README
6. `docs/boundaries.md`
7. the owning mechanic route

## Boundaries

- Do not make loaded sibling catalogs SDK source truth.
- Do not hide missing owner surfaces behind permissive path search.
- Keep truth labels visible: source, generated, candidate, manual, reviewed,
  activated, advisory.
- Route source-meaning changes to the sibling owner.

## Validation

```bash
python scripts/validate_sdk_source_home.py
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests
```

## Closeout

State which sibling surface or truth-label boundary changed and which owner
remains stronger than the SDK facade.
