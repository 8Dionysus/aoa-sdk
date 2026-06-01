# SDK Source Home

`sdk/` is the source-authored home for SDK-owned shape in `aoa-sdk`.

The home exists so the repository has one obvious source body for SDK posture
instead of forcing agents to infer ownership only from `src/aoa_sdk/`,
`mechanics/`, root docs, and release helpers.

Its checked contract is `source_home.manifest.json`. The manifest names every
active source-home branch, the branch owner route, related implementation and
mechanic routes, validation routes, and stronger-owner stop lines.

## Operating Card

| Field | Route |
| --- | --- |
| role | source home for SDK-owned posture |
| input | public interface, facade boundary, runtime-entry, or distribution route pressure |
| output | branch route, checked home manifest, implementation route, mechanic route, or stronger-owner handoff |
| owner | `sdk/source_home.manifest.json` plus nearest branch `AGENTS.md` |
| next route | target branch, implementation surface, mechanic package, validator, or decision record |
| tools | `scripts/validate_sdk_source_home.py`, `scripts/validate_nested_agents.py`, and owner-specific tests |
| validation | `python scripts/validate_sdk_source_home.py` plus branch-specific checks |

## Active Source Branches

`sdk/` has four active branches:

- `sdk/public-interface/` for public API, CLI, and model contract posture.
- `sdk/facade-boundary/` for sibling-reader, compatibility, and truth-label
  boundaries.
- `sdk/runtime-entry/` for workspace, Codex, and reviewed closeout entry
  posture.
- `sdk/distribution/` for package, release, and public support promises.

| Family | Path | Routes To |
| --- | --- | --- |
| Python API contract posture | `sdk/public-interface/python-api/` | `src/aoa_sdk/api.py`, `src/aoa_sdk/__init__.py`, API tests |
| CLI contract posture | `sdk/public-interface/cli-contract/` | `src/aoa_sdk/cli/`, CLI tests |
| model contract posture | `sdk/public-interface/model-contract/` | `src/aoa_sdk/models.py`, root schemas, model tests |
| sibling surface readers | `sdk/facade-boundary/sibling-surface-readers/` | facade registries and boundary-bridge reader tests |
| compatibility policy | `sdk/facade-boundary/compatibility-policy/` | `src/aoa_sdk/compatibility/`, compatibility gates |
| truth-label posture | `sdk/facade-boundary/truth-label-posture/` | truth labels in models, docs, and tests |
| workspace context | `sdk/runtime-entry/workspace-context/` | workspace discovery and runtime-seam mechanics |
| Codex entrypoints | `sdk/runtime-entry/codex-entrypoints/` | Codex projection implementation and mechanics |
| closeout entrypoints | `sdk/runtime-entry/closeout-entrypoints/` | checkpoint and closeout mechanics |
| package contract | `sdk/distribution/package-contract/` | `pyproject.toml`, build checks |
| release posture | `sdk/distribution/release-posture/` | release-support mechanics and release docs |
| public support posture | `sdk/distribution/public-support/` | support/CI posture docs and checks |

## Source Home Contract

`sdk/source_home.manifest.json` is the machine-checkable atlas for this home.
It deliberately does not replace implementation files. It records:

- which branches are allowed directly under `sdk/`;
- which branch card owns local editing posture;
- which family README routes explain the source-home leaf;
- which implementation, mechanic, docs, or release surfaces carry behavior;
- which validators prove the home stayed coherent;
- which stronger owner handles pressure that does not belong in `aoa-sdk`.

The manifest should change when a branch or source-home family is added,
removed, renamed, or given a new validation route. It should not be used as a
shortcut for moving executable code into `sdk/`.

## Traversal

Start from the branch that names the pressure, then follow its local
`AGENTS.md`.

Use `src/aoa_sdk/` for importable Python implementation, `mechanics/` for
repeatable operations, `docs/` for public explanation and decisions,
`schemas/` for shared contract shape, `generated/` for derived companions,
and `tests/` for repo-wide regression.

## Stop Lines

- `sdk/` is not `src/aoa_sdk/`.
- `sdk/` is not `mechanics/`.
- `sdk/` is not a runtime worker home.
- `sdk/` is not a sibling-source owner.
- `sdk/source_home.manifest.json` is a route contract, not a generated reader
  and not a replacement for implementation files.
