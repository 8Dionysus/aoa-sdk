# AGENTS.md

Local guidance for `src/aoa_sdk/` in `aoa-sdk`. Read the root `AGENTS.md` first.
This directory owns typed control-plane facades for consumed AoA surfaces.

## Scope

Code here loads, validates, discloses, activates only when explicitly bounded, and hands off owner-owned surfaces.
Stay on the control plane: do not turn typed helpers into runtime services, route authorities, hidden policy engines, or sources of sibling-repo meaning.

## Local contract

- Preserve owner boundaries, truth labels, source refs, and activation state in every helper.
- Keep `manual-equivalent`, `suggested`, `loaded`, `activated`, and reviewed-only states distinct.
- Prefer explicit manifests and config over magic discovery.
- Keep imports cheap and testable; do not require sibling repos, live services, or private workspace state for basic imports.
- When topology, CLI behavior, compatibility, or reviewed closeout behavior changes, update docs and tests together.

## Validate

Common gates:

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q
python -m ruff check .
```
