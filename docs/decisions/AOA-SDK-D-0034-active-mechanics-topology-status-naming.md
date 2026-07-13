# Active Mechanics Topology Status Naming

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0034
- Original date: 2026-06-01
- Surface classes: topology, mechanics, validation
- SDK facets: mechanics topology, active naming, route validation
- Mechanic parents: all
- Guard families: active naming, root-surface hygiene, mechanics topology
- Posture: accepted

## Context

After part-local payload localization, root technical-district cleanup, root
route-card hardening, and the later Questbook source-store restoration, the active mechanics
topology no longer describes a skeleton or partial artifact movement.

The machine-readable topology still used `artifact-localization-in-progress`
and `partial`. Because `mechanics/topology.json` is an active routing surface,
those names were stale active truth, not historical provenance.

## Decision

Rename the active topology status to `active-part-localized-topology` and
require `payload_movement_status` to be `complete`.

The validator must fail if those active names drift back to skeleton,
in-progress, or partial-localization vocabulary.

Active route IDs also must not use migration vocabulary such as `legacy`,
`fallback`, `former`, `old-root`, or `skeleton`.

## Rationale

Active topology names should answer the operational map directly: the
mechanics parent set is active, payload belongs under part-local owners, and
historical root names live in provenance, decisions, or legacy indexes.

This follows the same route-law pressure as the rest of the refactor: a future
agent should see role, owner, state, and validation without reverse-engineering
whether an old migration label is still authoritative.

## Consequences

- `mechanics/topology.json` carries current active status vocabulary.
- `scripts/validate_mechanics_topology.py` rejects stale topology status names.
- Active route IDs cannot reuse legacy or migration vocabulary.
- `tests/test_mechanics_topology.py` protects the status and payload posture.
- Historical terms remain valid only in decisions, provenance, changelog, or
  legacy accounting.

## Source Surfaces

- `mechanics/topology.json`
- `scripts/validate_mechanics_topology.py`
- `tests/test_mechanics_topology.py`
- `mechanics/README.md`
- `mechanics/ARTIFACT_TOPOLOGY.md`

## Follow-Up Route

If future payload work introduces a new partial state, add a fresh decision
that names the new active state by route role instead of reusing skeleton or
migration vocabulary.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
