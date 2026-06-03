# AGENTS.md

## Applies To

Root `scripts/`.

## Role

Root scripts are repo-wide builders, validators, release gates, and shared
control-plane utilities.

## Read Before Editing

1. Root `AGENTS.md`
2. `DESIGN.md`
3. `mechanics/README.md`
4. The owning mechanic `VALIDATION.md` if a script serves one mechanic part

## Boundaries

- Keep single-mechanic scripts under
  `mechanics/<parent>/parts/<part>/scripts/`.
- Keep root scripts deterministic and runnable from the repository root.
- Route moved mechanic payload through its current part-local owner path.
- Builders must name their source inputs and generated outputs.
- Keep source-home validators repo-wide when they protect top-level homes such
  as `sdk/`.

## Validation

```bash
python -m ruff check scripts
python scripts/validate_sdk_source_home.py
python scripts/validate_mechanics_topology.py
python scripts/build_source_topology_index.py --check
python scripts/validate_source_topology_index.py
python scripts/release_check.py
```

## Closeout

State whether the script is repo-wide or part-owned. If part-owned, move it
under the part and update package `PROVENANCE.md`, part `VALIDATION.md`, and
`mechanics/topology.json` in the same change.
