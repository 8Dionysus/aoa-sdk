# Skill Environment Inspector Contract

## Allowed Operations

- Read owner-authored skill ecosystem surfaces through compatibility rules.
- Inspect one exact capability and its typed incoming and outgoing relations.
- Keep user, repository, legacy workspace, source-export, and owner-source
  roots distinct.
- Compare admitted copies with their exact owner source tree.
- Report missing admission, drift, unmanaged entries, and cross-scope duplicates.

## Home-Port Compatibility

The shared grammar belongs to `aoa-skills:schemas/skill-home-port.schema.json`.
The inspector dispatches by `schema_version`:

- v1 retains repository `projection` inspection and the public
  `SkillHomePortManifest` constructor.
- v2 reads the owner home and its fixed Codex user exposure. Its complete,
  ordered bundle selection keeps the original v2 meaning.
- v3 reads the owner home and zero or more consumer exposures. Each exposure
  names a unique runtime/scope/profile target and a nonempty subset of declared
  bundles. Eligibility does not select a profile or install a package.

Use `AnySkillHomePortManifest` for version-dispatched parsing; v2 and v3 have
their own public models. Invalid targets, duplicate or unknown selections,
unknown fields, and owner paths escaping their root are rejected. Inspection
reports missing or symlinked owner/admission/source files without following
them or attempting repair.

For `owner-source` observations, `admitted` records the manifest's declaration,
not runtime admission or independent verification of its rationale. These
entries do not participate in installed-copy duplicate counts. A same-name
repository copy of a Codex user-exposed bundle is still reported as competing;
foreign exposures do not imply Codex repository conflicts.

The existing user-root comparison consumes the portable `user-default`
profile. Complete `os-user-default` managed-copy and owner-link receipt
verification belongs to workspace bootstrap and the `aoa-skills` profile
assembler. Inspector output alone cannot establish OS profile currentness.

## Stop-Lines

- Do not rank, retrieve, dispatch, activate, deactivate, or compose capabilities.
- Do not create skill-session state or infer execution from filesystem presence.
- Do not treat source export, an owner bundle, or exposure eligibility as an
  installed host capability.
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
