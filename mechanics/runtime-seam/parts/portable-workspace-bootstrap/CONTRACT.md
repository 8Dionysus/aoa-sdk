# Portable Workspace Bootstrap Contract

## Guarantees

- Loads one exact owner-authored install profile through compatibility rules.
- Separates dry-run readiness from executed bootstrap.
- Copies user-scoped profile entries into the explicit or host-selected user
  root and verifies full tree parity.
- Reports conflict unless replacement is explicitly authorized with
  `--overwrite`.
- Rejects repository-scoped profiles without planning or applying repository
  projection steps.
- Leaves workspace `AGENTS.md`, workspace-wide skill projections, repository
  homes, and legacy copies untouched.

## Non-Goals

- It does not create source-owned sibling repo content.
- It does not infer or build a repository skill home.
- It does not make workspace bootstrap a host deployment system.
- It does not make copied skill files stronger than the owning skill repo.
