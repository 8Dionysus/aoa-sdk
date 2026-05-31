# AGENTS.md

## Applies to

Everything under `mechanics/`.

## Role

`mechanics/` is the SDK operation topology layer. It names repeatable
cross-surface SDK operations and points back to the source, docs, schemas,
examples, generated companions, scripts, and tests that already carry payload.

Mechanics are route maps. They are not the importable SDK source home.

## Read before editing

1. Root `AGENTS.md`
2. `DESIGN.md`
3. `DESIGN.AGENTS.md`
4. `docs/decisions/README.md`
5. `mechanics/README.md`
6. `mechanics/TOPOLOGY_PREP.md`
7. `mechanics/topology.json`
8. The package-local `AGENTS.md` and README for each touched mechanic
9. The stronger source surface named by the mechanic card

## Boundaries

- Stay on the control plane.
- Keep `src/aoa_sdk/` as the importable Python source home.
- Keep generated companions lower authority than their builders and sources.
- Keep sibling-owned meaning in the sibling repository.
- Top-level package names follow the shared AoA mechanics vocabulary. A
  repo-local top-level mechanic needs evidence that it cannot be a part of an
  existing shared parent.
- Every tracked `src/aoa_sdk/*` family routes through
  `mechanics/topology.json#source_family_routes`. Add or update that route
  before claiming a new source family is covered.
- File-family pressure routes through `PARTS.md`; it does not create a parent
  package by itself.
- Do not create physical `parts/` payload directories until a later landing
  moves or adds reviewed payload with a package-local validator.
- Do not treat topology cards as proof that a source surface has moved.

## Validation

Run the narrow topology gate after editing this tree:

```bash
python scripts/validate_mechanics_topology.py
```

For structural route changes, also run:

```bash
python scripts/generate_decision_indexes.py --check
python -m pytest -q tests/test_mechanics_topology.py tests/test_validate_nested_agents.py
```

Release-facing or root-route changes should continue through
`python scripts/release_check.py`.

## Closeout

Report which mechanic package changed, whether any payload moved, which source
surfaces remain stronger, and which validator proved the topology.
