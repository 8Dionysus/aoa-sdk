# Portable Workspace Bootstrap

## Role

`portable-workspace-bootstrap` prepares a non-default AoA workspace using the
SDK workspace manifest, required repo list, root `AGENTS.md` route, and skill
install profile without treating generated sibling content as SDK-owned truth.

## Input

- `src/aoa_sdk/workspace/bootstrap.py`
- `src/aoa_sdk/workspace/roots.py`
- fixture workspace repos and generated foundation profiles
- `aoa workspace bootstrap ...` CLI calls

## Output

- readiness reports for missing required repos
- explicit dry-run versus executed bootstrap status
- installed workspace skill links or copies
- root `AGENTS.md` install/update reports

## Owner

`aoa-sdk` owns the bootstrap helper and report shape. Sibling repositories own
their generated foundation profiles, skill meanings, and source content.

## Validation

Use `VALIDATION.md`.
