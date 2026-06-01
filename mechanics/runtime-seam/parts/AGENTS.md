# AGENTS.md

## Runtime Seam Parts Route

Use these parts when changing SDK workspace path resolution, generated
control-plane capsule refs, portable workspace bootstrap, or source/runtime
mirror read boundaries.

Active part homes:

- `workspace-root-resolution/` resolves workspace roots and repo path origins.
- `portable-workspace-bootstrap/` prepares non-default workspace installs
  without owning sibling content.
- `control-plane-capsule/` builds and validates the compact routing capsule.
- `runtime-mirror-boundary/` keeps source checkout and runtime mirror reads
  explicit.

Do not hide path guessing or make runtime mirrors stronger than source-owned
repositories.
