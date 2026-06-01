# Portable Workspace Bootstrap Contract

## Guarantees

- Reports missing required repos before mutation.
- Separates dry-run readiness from executed bootstrap.
- Installs skill routes from source-owned skill profiles without changing their
  meaning.
- Supports explicit install modes and overwrite behavior.

## Non-Goals

- It does not create source-owned sibling repo content.
- It does not make workspace bootstrap a host deployment system.
- It does not make copied skill files stronger than the owning skill repo.
