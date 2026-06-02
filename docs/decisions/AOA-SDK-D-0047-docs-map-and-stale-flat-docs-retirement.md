# Docs Map And Stale Flat Docs Retirement

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0047
- Original date: 2026-06-02
- Surface classes: docs, route-law, topology, validation
- SDK facets: docs map, root docs, decision lane
- Mechanic parents: all
- Guard families: root-surface hygiene, docs routes, decision drift
- Posture: accepted

## Context

Root `docs/` had no entry map. Readers had to infer the role of each flat
file from its name.

Two flat files no longer carried active authority:

- `docs/AGENTS_ROOT_REFERENCE.md` preserved a long dump of old root guidance,
  including operational commands and checkpoint/closeout protocol that now
  belongs in active route cards and mechanic-local docs.
- `docs/ecosystem-impact.md` described the repository birth pressure, but its
  current useful claims are already carried by `README.md`, `ROADMAP.md`,
  `docs/boundaries.md`, and the historical `docs/blueprint.md`.

`docs/decisions/README.md` also carried a manual list of active mechanics
decisions. That list had the same drift shape as live changelog counters: it
became stale every time a new decision landed.

## Options Considered

- Keep the flat docs because the current topology validator allowlisted them.
- Move the old root reference into a subdistrict.
- Add a docs map, retire stale flat docs, and route decision lookup through
  generated indexes.

## Decision

Add `docs/README.md` as the docs entry map.

Retire `docs/AGENTS_ROOT_REFERENCE.md` and `docs/ecosystem-impact.md` from the
active docs tree.

Replace the manual active-decision roster in `docs/decisions/README.md` with a
lookup route to generated decision indexes.

Update root references and validators after the semantic choice, not as the
reason for the choice.

## Rationale

Root docs should route. They should not preserve old operational dumps or
one-off origin prose when current owner surfaces already carry the meaning.

The current checkpoint, closeout, release, workspace, and compatibility routes
are stronger when they live in root `AGENTS.md`, mechanic package cards, part
docs, and part validation cards. A preserved dump in flat `docs/` competes
with those owners and makes future readers re-arbitrate stale guidance.

Decision lookup is already solved by generated indexes. Keeping a second
manual list in `docs/decisions/README.md` creates predictable drift without
adding authority.

## Consequences

- `docs/` now has a human and agent entrypoint.
- Old root guidance no longer appears as a competing active docs surface.
- Birth-pressure prose no longer sits beside current boundary and versioning
  docs as if it were current source truth.
- Decision README becomes stable entry prose instead of a live roster.
- Validators and tests must follow this docs topology, but they do not define
  it.

## Source Surfaces

- `docs/README.md`
- `docs/AGENTS.md`
- `docs/decisions/README.md`
- `AGENTS.md`
- `README.md`
- `ROADMAP.md`
- `scripts/validate_mechanics_topology.py`

## Follow-Up Route

Future root docs additions should first decide whether the file is a true
repo-wide docs surface, a historical seed note, a decision rationale entry, or
a mechanic-owned part doc.

Use generated decision indexes for lookup instead of adding another manual
ledger.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py
python -m pytest -q tests/test_docs_routes.py tests/test_mechanics_topology.py tests/test_validate_nested_agents.py
```
