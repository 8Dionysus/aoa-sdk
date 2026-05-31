# Workspace Topology Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| workspace-root-resolution | `.aoa/workspace.toml`, `src/aoa_sdk/workspace/discovery.py`, `src/aoa_sdk/workspace/roots.py` | only if root-resolution docs and tests become too dense for the source lane |
| control-plane-capsule | `generated/workspace_control_plane.min.json`, `scripts/build_workspace_control_plane.py` | only with a package-local parity validator |
| portable-bootstrap | `src/aoa_sdk/workspace/bootstrap.py`, `docs/workspace-layout.md` | only if bootstrap contracts need reusable examples or schemas |
