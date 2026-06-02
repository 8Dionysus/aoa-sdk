# AGENTS.md

## Applies To

Root `docs/` surfaces, excluding stronger nested cards such as
`docs/decisions/AGENTS.md`.

## Role

Root docs are public route, boundary, versioning, workspace, design-reference,
and historical context surfaces.

## Read Before Editing

1. Root `AGENTS.md`
2. `DESIGN.md`
3. `DESIGN.AGENTS.md`
4. `mechanics/README.md`
5. The owning mechanic package and part when a doc is part-specific

## Boundaries

- Keep part-specific operational docs under
  `mechanics/<parent>/parts/<part>/docs/`.
- Keep root release docs as thin route doors when a release-support part owns
  the detailed runbook or posture.
- Keep historical docs explicit as history; do not make seed notes active
  source truth.
- Route moved mechanic payload through its current part-local owner home.

## Validation

```bash
python -m pytest -q tests/test_docs_routes.py tests/test_design_surfaces.py
python scripts/validate_nested_agents.py
```

## Closeout

Report whether the edited doc is a root public route, a historical note, or a
mechanic-owned surface that should move into a part-local docs lane.
