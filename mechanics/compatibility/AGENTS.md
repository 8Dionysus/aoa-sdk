# AGENTS.md

## Applies to

`mechanics/compatibility/`.

## Role

Route the SDK-local compatibility mechanic for consumed sibling surface paths,
stable SDK surface IDs, sibling canaries, and version posture.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/compatibility/README.md`
- `docs/versioning.md`
- `docs/boundaries.md`
- `src/aoa_sdk/compatibility/policy.py`
- `scripts/sibling_canary_matrix.json`

## Boundaries

- Stay on the control plane.
- Do not add hidden fallback for missing owner surfaces.
- Do not make SDK surface IDs imply ownership of sibling topology.
- Do not preserve legacy physical paths after the stronger owner has moved.

## Validation

```bash
python scripts/validate_mechanics_topology.py
aoa compatibility check /srv/AbyssOS/aoa-sdk
aoa compatibility check /srv/AbyssOS/aoa-sdk --repo aoa-skills --json
python -m pytest -q tests/test_compatibility.py tests/test_sibling_canary.py
```

## Closeout

Report the canonical path, the stable SDK surface ID, and whether any missing
surface is accepted drift or a failure.
