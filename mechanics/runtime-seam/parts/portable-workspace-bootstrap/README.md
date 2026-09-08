# Portable Workspace Bootstrap

## Role

`portable-workspace-bootstrap` plans or applies one exact user-scoped
`aoa-skills` install profile into a host-selected Codex skill root without
turning the SDK into a workspace, repository-home, or runtime owner. The
default `os-user-default` path transports the current `aoa-skills` owner
installer; explicit portable v2 profiles remain on the SDK copy planner.

## Input

- `src/aoa_sdk/workspace/bootstrap.py`
- `src/aoa_sdk/workspace/os_profile.py`
- `src/aoa_sdk/contracts/workspace.py`
- `src/aoa_sdk/workspace/roots.py`
- current `aoa-skills` resolved install profiles and portable exports
- `aoa workspace bootstrap ...` CLI calls

The CLI defaults to the owner `os-user-default` profile. Repeat
`--source-root OWNER=PATH` to bind a clean owner checkout and use `--os-root`
to set the federation root supplied to the owner command. The default action
is the owner's read-only plan; pass `--check` for installed-state verification
or `--execute` for the owner-controlled install.
These OS-installer options are rejected when an explicit portable profile is
selected, rather than being silently ignored.

## Output

- readiness reports for exact owner-profile copies
- strict owner-installer transport reports with opaque owner payloads,
  subprocess exit codes, bounded diagnostics, and execute/check state
- explicit dry-run versus executed bootstrap status
- verified user-root copies, conflicts, and explicit overwrite plans
- repository-profile rejection with an owner-builder return route
- owner-plan payloads remain opaque and carry explicit transport and
  verification states

## Owner

`aoa-sdk` owns the bootstrap helper and report shape. Sibling repositories own
their skill meanings, source content, home admission, and repository
projections. The host owns the user root and runtime discovery.

## Validation

Use `VALIDATION.md`.
