# Runtime Seam Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| workspace-root-resolution | `mechanics/runtime-seam/parts/workspace-root-resolution/`, `.aoa/workspace.toml`, `src/aoa_sdk/workspace/discovery.py`, `src/aoa_sdk/workspace/roots.py` | active; resolves workspace roots and repo path origins without hidden guessing |
| control-plane-capsule | `mechanics/runtime-seam/parts/control-plane-capsule/`, `generated/workspace_control_plane.min.json`, `scripts/build_workspace_control_plane.py` | active; builds and validates the compact routing capsule |
| portable-workspace-bootstrap | `mechanics/runtime-seam/parts/portable-workspace-bootstrap/`, `src/aoa_sdk/workspace/bootstrap.py`, `docs/workspace-layout.md` | active; prepares non-default workspace installs without owning sibling content |
| runtime-mirror-boundary | `mechanics/runtime-seam/parts/runtime-mirror-boundary/`, `docs/workspace-layout.md`, live-workspace tests | active; keeps source checkout and runtime mirror reads explicit |
