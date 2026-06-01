# Skill Runtime Bridge Part Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0017
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, boundary bridge, skill runtime bridge
- Mechanic parents: boundary-bridge
- Guard families: mechanics topology, part validation, docs routes, active naming
- Posture: accepted

## Context

After the Checkpoint closeout context carry slice, Boundary Bridge still carried
skill-runtime bridge payload in root districts:

- `docs/skill-runtime-recommendation-gap.md`
- `docs/skill-runtime-recommendation-gap-fix-spec.md`
- `tests/test_skills.py`

These surfaces are not repo-wide design law. They describe one Boundary Bridge
part: how SDK skill reports distinguish router recommendations from host
actionability while `aoa-skills` keeps canonical skill meaning.

## Decision

Localize the skill-runtime bridge payload into:

- `mechanics/boundary-bridge/parts/skill-runtime-bridge/`

Keep `src/aoa_sdk/skills/`, `src/aoa_sdk/cli/`, and `src/aoa_sdk/models.py`
in importable SDK implementation homes. The part owns docs, validation route,
and artifact placement for the bridge; it does not become a source package.

## Rationale

The old root titles named a gap and a fix spec. The active part name says the
operation: skill runtime signals cross from router/host inventory into SDK
reports without moving skill meaning into SDK.

This keeps the active path agent-operable:

- input: `aoa skills ...` pressure and host inventory
- output: host actionability labels and runtime session reports
- owner: SDK bridge behavior
- next route: `aoa-skills` for canonical skill meaning and export truth

## Consequences

- Root `docs/` and `tests/` no longer own active skill-runtime bridge payload.
- Old root names live in `mechanics/boundary-bridge/PROVENANCE.md` and
  `mechanics/ARTIFACT_TOPOLOGY.md`, not as active fallbacks.
- Boundary Bridge now has two functioning part-local payload homes:
  `skill-runtime-bridge` and `owner-layer-signal-handoff`.
- CLI/API source and model code remain in `src/aoa_sdk/`.

## Source Surfaces

- `mechanics/boundary-bridge/README.md`
- `mechanics/boundary-bridge/PARTS.md`
- `mechanics/boundary-bridge/PROVENANCE.md`
- `mechanics/boundary-bridge/parts/skill-runtime-bridge/`
- `mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py`
- `mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_reference_contracts.py`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `README.md`

## Follow-Up Route

Continue root technical district audit for Checkpoint test placement, Questbook
payload, and cross-mechanic public contracts.

## Verification

```bash
python -m pytest -q mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_reference_contracts.py tests/test_docs_routes.py
python scripts/validate_mechanics_topology.py
```
