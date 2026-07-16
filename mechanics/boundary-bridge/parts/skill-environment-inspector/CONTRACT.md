# Skill Environment Inspector Contract

## Allowed Operations

- Read owner-authored skill ecosystem surfaces through compatibility rules.
- Inspect one exact capability and its typed incoming and outgoing relations.
- Keep user, repository, legacy workspace, and source-export roots distinct.
- Compare admitted copies with their exact owner source tree.
- Report missing admission, drift, unmanaged entries, and cross-scope duplicates.

## Stop-Lines

- Do not rank, retrieve, dispatch, activate, deactivate, or compose capabilities.
- Do not create skill-session state or infer execution from filesystem presence.
- Do not treat source export as an installed host capability.
- Do not admit `.agents/skills` as a repository home without
  `skills/port.manifest.json`.
- Do not repair, install, or delete observed roots during inspection.
- Do not merge same-name entries from different scopes into one availability
  result.

## Public Source

- `src/aoa_sdk/skills/inspection.py`
- `src/aoa_sdk/skills/discovery.py`
- `src/aoa_sdk/contracts/skills.py`
- `src/aoa_sdk/cli/skills.py`

The retired `skill-runtime-bridge` remains available only through repository
history and AOA-SDK-D-0067.
