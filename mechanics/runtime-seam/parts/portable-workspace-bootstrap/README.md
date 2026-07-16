# Portable Workspace Bootstrap

## Role

`portable-workspace-bootstrap` plans or applies one exact user-scoped
`aoa-skills` install profile into a host-selected Codex skill root without
turning the SDK into a workspace, repository-home, or runtime owner.

## Input

- `src/aoa_sdk/workspace/bootstrap.py`
- `src/aoa_sdk/workspace/roots.py`
- current `aoa-skills` resolved install profiles and portable exports
- `aoa workspace bootstrap ...` CLI calls

## Output

- readiness reports for exact owner-profile copies
- explicit dry-run versus executed bootstrap status
- verified user-root copies, conflicts, and explicit overwrite plans
- repository-profile rejection with an owner-builder return route

## Owner

`aoa-sdk` owns the bootstrap helper and report shape. Sibling repositories own
their skill meanings, source content, home admission, and repository
projections. The host owns the user root and runtime discovery.

## Validation

Use `VALIDATION.md`.
