# AGENTS.md

Local guidance for `schemas/` in `aoa-sdk`. Read the root `AGENTS.md` first.
This directory owns SDK helper contract schemas.

## Scope

Schemas here define helper registries, bindings, packets, adapters, and control-plane contracts consumed by SDK code and generated summaries.
They are owner-subordinate and must not convert sibling-repo meaning into SDK-owned doctrine.

## Local contract

- Treat schema changes are contract changes.
- Keep `$schema`, `$id`, required fields, enums, version suffixes, and generated registry expectations aligned.
- Pair schema changes with source code, generated artifacts, docs, and tests.
- Preserve truth labels and owner refs; do not flatten multi-axis or reviewed-only states into a magic readiness score.
- Avoid private paths, secrets, and live workspace assumptions in defaults or examples.

## Validate

Common gates:

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q
```
