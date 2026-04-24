# AGENTS.md

Local guidance for `generated/` in `aoa-sdk`. Read the root `AGENTS.md` first.
This directory carries generated control-plane summaries.
Generated artifacts are lower authority than their sources.

## Scope

Generated files such as `workspace_control_plane.min.json` and helper registries make the SDK's consumed surfaces quick to inspect.
They do not own skill, eval, memo, playbook, routing, role, or runtime meaning.

## Local contract

- Do not hand-edit minified JSON when a builder owns it.
- Update source docs, schemas, or scripts first, then regenerate.
- Keep generated artifacts deterministic, public-safe, and owner-subordinate.
- If generated output changes without a source change, explain why it is legitimate rather than silent drift.

## Validate

Common gates:

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q
```
