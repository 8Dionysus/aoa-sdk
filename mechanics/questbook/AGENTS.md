# AGENTS.md

## Applies to

This card applies to `mechanics/questbook/` and all descendants.

## Role

Questbook is the SDK operation package for source quest record placement,
public obligation indexing, lifecycle posture, and dispatch-reader posture.

Stay on the control plane. This mechanic makes obligations visible and
returnable; it does not turn a quest into a proof verdict, owner acceptance,
runtime action, release readiness, or Agon authority.

## Read Before Editing

Read root `AGENTS.md`, `DESIGN.md`, `DESIGN.AGENTS.md`, `QUESTBOOK.md`,
`quests/README.md`, this package `README.md`, this package `ROADMAP.md`,
`PARTS.md`, and the nearest part card.

## Boundaries

- Source quest records live in root `quests/`.
- The human open-obligation index lives in root `QUESTBOOK.md`.
- SDK helper contracts live in their owning mechanics parts.
- Generated quest readers must be derived from source records and must land
  with builder and validator routes.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py --strict-advisory --fail-on-untracked
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
```
