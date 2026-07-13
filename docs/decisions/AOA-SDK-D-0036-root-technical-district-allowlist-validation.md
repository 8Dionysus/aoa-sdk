# Root Technical District Allowlist Validation

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0036
- Original date: 2026-06-01
- Surface classes: topology, validation guard, mechanics, root technical districts
- SDK facets: mechanics topology, root district hygiene, active naming, artifact placement
- Mechanic parents: all
- Guard families: root-surface hygiene, mechanics topology, active naming, validator authority
- Posture: accepted

## Context

After mechanic-owned payload moved out of root technical districts, the root
surface still needed a durable guard against quiet re-growth.

Manual inspection showed a small active root set:

- `docs/` for route-wide docs, decisions, release doors, and workspace docs.
- `generated/` for the root-published workspace control-plane companion.
- `schemas/` for the root workspace control-plane schema.
- `scripts/` for repo-wide builders, validators, and release gates.
- `tests/` for repo-wide regression, fixtures, and validator tests.
- `quests/` for Questbook source quest records in lane/state form.

The former single-mechanic root districts `config/`, `examples/`,
`manifests/`, `githooks/`, and `systemd/` no longer have active root
ownership. Root `quests/` is active only as the Questbook source-record
district restored by `AOA-SDK-D-0042`.

## Decision

Teach `scripts/validate_mechanics_topology.py` to treat root technical
districts as an explicit allowlist.

The validator rejects unexpected files in active root districts and rejects
re-created root districts that should stay absent. New single-mechanic payload
must move to `mechanics/<parent>/parts/<part>/...` unless a decision-backed
root contract reopens the path.

## Rationale

The active surface must name its owner and route. A root `docs/foo.md` or
`scripts/foo.py` can hide whether the file is repo-wide, public, tooling-facing,
or actually owned by one mechanic. A part-local path makes the operation,
owner, next route, and validation home visible before an agent reads the file.

This follows the operating-map shape used by the refactored sibling repos:
root surfaces dispatch, part homes carry payload, generated/readout surfaces
stay weaker than owner files, and legacy names do not become active routes.

## Consequences

- Root technical districts now fail mechanics topology validation when an
  unlisted file appears.
- `config/`, `examples/`, `manifests/`, `githooks/`, and `systemd/`
  now fail validation if they reappear at root without an explicit route-law
  change.
- `quests/` is allowlisted only for Questbook source records and local route
  cards.
- `tests/test_mechanics_topology.py` proves the current root district set is
  fully allowlisted.
- Future root additions must either prove repo-wide/public/tooling ownership or
  move into a topologically named part-local mechanics route.

## Source Surfaces

- `scripts/validate_mechanics_topology.py`
- `tests/test_mechanics_topology.py`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/README.md`

## Follow-Up Route

When a future root file is proposed, first choose whether it is a true root
contract or a part-local mechanic payload. If it is root-owned, update the
allowlist and the route documentation in the same decision-backed slice.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
