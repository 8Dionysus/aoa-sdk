# AGENTS.md

## Applies to

`mechanics/codex-projection/legacy/`.

## Role

Legacy preserves former Codex Projection mechanics parent names and migration
receipts after their active route has been distilled into canonical parts.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/codex-projection/AGENTS.md`
- `mechanics/codex-projection/PROVENANCE.md`
- `mechanics/codex-projection/legacy/INDEX.md`

## Boundaries

- Stay on the control plane.
- Do not make SDK Codex reads a Codex runtime or deploy authority.
- Do not treat former parent names as active route ids.
- Do not add a legacy entry without naming the active Codex Projection part it
  now pressures.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

## Closeout

Report legacy index changes, active Codex Projection routes consulted, and
whether any former parent name remains outside a legacy district.
