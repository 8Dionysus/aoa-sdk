# Boundary Bridge Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| typed-facades | `src/aoa_sdk/*/registry.py`, `src/aoa_sdk/api.py`, `src/aoa_sdk/cli/` | only if facade families need shared owner maps |
| surface-loaders | `src/aoa_sdk/loaders/`, `src/aoa_sdk/compatibility/policy.py` | only if loader behavior starts carrying reusable crossing contracts |
| truth-labels | `src/aoa_sdk/models.py`, facade model tests | only if labels become cross-cutting schemas |
| compatibility-policy | `src/aoa_sdk/compatibility/policy.py`, `docs/versioning.md`, `scripts/sibling_canary_matrix.json` | migrated from the over-specific `compatibility` parent; remains a bridge part |
| skill-runtime-bridge | `.agents/skills/`, `src/aoa_sdk/skills/`, skill runtime docs | migrated from the over-specific `skill-routing` parent; `aoa-skills` keeps skill meaning |
| surface-detection-handoff | `docs/aoa-surface-detection-*.md`, `src/aoa_sdk/surfaces/` | migrated from the over-specific `surface-detection` parent; hints stay advisory |
| owner-return-routes | `docs/boundaries.md`, route tests | only if handoff receipts become package-local artifacts |
