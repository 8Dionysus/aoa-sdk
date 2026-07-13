# Root Technical District Route Card Hardening

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0032
- Original date: 2026-06-01
- Surface classes: topology, agent guidance, validation guard
- SDK facets: nested agents, root technical districts, mechanics topology
- Mechanic parents: boundary-bridge, release-support, runtime-seam
- Guard families: nested agents, root-surface hygiene, active naming
- Posture: accepted

## Context

After part-local artifact moves, root `docs/`, `scripts`, `tests`, and
checked-in `.agents/skills/` still existed as high-risk editable districts
without local route cards.

That left the rule "single-mechanic payload goes under mechanics parts" in
root prose and validators, but not at the nearest edit surface.

## Decision

Add local route cards for:

- `docs/AGENTS.md`
- `scripts/AGENTS.md`
- `tests/AGENTS.md`
- `.agents/skills/AGENTS.md`

Register those cards in `scripts/validate_nested_agents.py` and list them in
`DESIGN.AGENTS.md`.

## Rationale

The active surface should give the next agent a clear route before they add a
file. Root docs, scripts, tests, and skill exports are allowed only when they
are repo-wide, public-route, shared, or consumed-export surfaces. The nearest
card must say when a file belongs in a part-local mechanics home instead.

## Consequences

- Root high-risk districts now have executable local guidance.
- The nested AGENTS validator protects these route cards.
- Missing-surface reporting should no longer treat these root districts as
  ungoverned.

## Source Surfaces

- `docs/AGENTS.md`
- `scripts/AGENTS.md`
- `tests/AGENTS.md`
- `.agents/skills/AGENTS.md`
- `scripts/validate_nested_agents.py`
- `DESIGN.AGENTS.md`

## Follow-Up Route

Keep future root districts either route-carded and validator-registered, or
remove them when they are empty after a part-local move.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
