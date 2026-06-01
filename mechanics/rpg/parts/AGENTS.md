# AGENTS.md

## Applies to

Functioning RPG parts under `mechanics/rpg/parts/`.

## Role

These parts hold active SDK RPG payload after it leaves root districts. They
route typed consumer APIs and transport path expectations while `src/aoa_sdk/rpg`
remains the importable source home.

## Boundaries

- Stay on the control plane.
- Do not turn typed reads into gameplay, frontend, runtime, quest, progression,
  or state authority.
- Keep canonical owner refs and generated transport paths visible.
- Keep old root paths in `mechanics/rpg/PROVENANCE.md` or
  `mechanics/ARTIFACT_TOPOLOGY.md`, not as active routes.

## Validation

```bash
python -m pytest -q mechanics/rpg/parts/typed-consumer-api/tests/test_typed_consumer_api.py mechanics/rpg/parts/surface-path-transport/tests/test_surface_path_transport.py
python scripts/validate_mechanics_topology.py
```

## Closeout

Report whether typed consumer behavior, surface-path transport expectations,
owner refs, or validation changed.
