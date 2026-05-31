# Runtime Seam Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| workspace-root-resolution | `.aoa/workspace.toml`, `src/aoa_sdk/workspace/discovery.py`, `src/aoa_sdk/workspace/roots.py` | only if root-resolution contracts need part-local examples |
| control-plane-capsule | `generated/workspace_control_plane.min.json`, `scripts/build_workspace_control_plane.py` | only with package-local parity generation |
| portable-bootstrap | `src/aoa_sdk/workspace/bootstrap.py`, `docs/workspace-layout.md` | only if bootstrap contracts need stable fixtures |
| runtime-mirror-boundary | `docs/workspace-layout.md`, live-workspace tests | only if mirror policy becomes a reusable contract |
| local-automation-seam | `githooks/`, `systemd/` | only if hook/unit artifacts move out of their owner districts |
