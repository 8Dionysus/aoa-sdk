# Questbook Source Store Restoration

## Status

Accepted.

Supersedes `AOA-SDK-D-0033`.

## Index Metadata

- Decision ID: AOA-SDK-D-0042
- Original date: 2026-06-01
- Surface classes: topology, mechanics, quest source store, root district
- SDK facets: mechanics topology, questbook, root quests, active naming
- Mechanic parents: questbook, agon, checkpoint
- Guard families: root source store, parent boundary, lifecycle posture, validation
- Posture: accepted

## Context

The first artifact-localization pass treated root `quests/` like ordinary
single-mechanic payload and moved Agon quest notes into Agon helper parts.
That contradicted the sibling pattern in `Agents-of-Abyss`, `aoa-memo`,
`aoa-evals`, `aoa-skills`, `aoa-techniques`, and `aoa-agents`.

In those repositories, root `quests/` is a lane-first source quest record
district. The `mechanics/questbook/` package owns source-store law, lifecycle
posture, public-index posture, generated-reader posture, and validation. It
does not replace the root source store.

## Decision

Restore root `quests/` as the active SDK source quest record district.

Restore `mechanics/questbook/` as an active parent package with three current
parts:

- `quest-source-store`;
- `public-obligation-index`;
- `lifecycle-dispatch-posture`.

Move SDK Agon quest notes back to `quests/agon/ready/`. Keep helper contracts,
generated companions, schemas, scripts, and tests in their owning
`mechanics/agon/parts/*` homes.

## Rationale

Quest records are not helper payload. They are durable obligation source
records and must remain visible at a stable root route so agents can find open
work without reading every part-local helper directory.

This matches the operational map used by sibling repos: source records,
public index, generated readers, owner parts, and validation are separate
surfaces.

## Consequences

- `AOA-SDK-D-0033` is superseded.
- The explicit active package set returns to 12 parents.
- Root `quests/` is allowed only as a quest source store, not as a generic
  payload district.
- `QUESTBOOK.md` becomes the human open-obligation index.
- Future generated quest readers need a source-derived builder, validator, and
  generated contract before landing.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
