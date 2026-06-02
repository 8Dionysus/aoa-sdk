# Root README Front Door

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0045
- Original date: 2026-06-02
- Surface classes: docs, route-law, validation
- SDK facets: root docs, control-plane routing, validation authority
- Mechanic parents: all
- Guard families: root-surface hygiene, docs routes
- Posture: accepted

## Context

The root `README.md` had grown into a mixed front door, current-state
inventory, command sheet, generated-surface roster, and mechanic detail index.
That made the first page hard to read and made tests preserve the wrong
authority: executable validation and part-local detail were being pinned in the
public entry surface instead of in `AGENTS.md`, package route cards, part
`VALIDATION.md`, release docs, and generated companions.

The adjacent root docs already name clearer owner roles. `AGENTS.md` carries
local route law and executable checks. `DESIGN.md` and `DESIGN.AGENTS.md`
explain system form and agent-facing form. `ROADMAP.md` carries current
direction. `QUESTBOOK.md` summarizes durable obligations. `sdk/` and
`mechanics/` now have their own checked route cards and validators.

## Options Considered

- Keep the root README as the detailed current-state inventory.
- Move the command and inventory blocks into another root document.
- Make the root README a compact public front door and keep operational
  authority in the owning route surfaces.

## Decision

Make `README.md` a compact, command-free public front door.

The README names what `aoa-sdk` does, points to owner surfaces, and explains
the control-plane check a reader should perform before editing. It does not
embed executable validation commands, full current-state batteries, generated
schema/example rosters, or mechanic-local command examples.

Executable validation authority stays in `AGENTS.md`, nearest nested
`AGENTS.md`, part `VALIDATION.md`, release docs, and owning tests. Detailed
mechanic routes stay in `mechanics/`; checked SDK posture stays in `sdk/`;
current direction stays in `ROADMAP.md`; durable rationale stays in decision
records.

## Rationale

A root README should help a human or agent choose the correct owner surface.
It should not become a second topology map or a second runbook.

Keeping command examples out of the public front door prevents test contracts
from forcing stale operations back into the first page. It also keeps the
repository aligned with the source-home and mechanics split: root routes,
source-home routes, mechanic routes, and part validation each carry their own
level of truth.

## Consequences

- `README.md` becomes easier to scan and safer as a public entrypoint.
- `tests/test_docs_routes.py` now asserts route-only README behavior instead
  of requiring command blocks and long path rosters.
- `QUESTBOOK.md` points to validation route owners instead of embedding a
  second command battery.
- Future root-doc changes should add links to owner surfaces, not copy their
  executable details into the front door.

## Source Surfaces

- `README.md`
- `AGENTS.md`
- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `ROADMAP.md`
- `QUESTBOOK.md`
- `sdk/README.md`
- `mechanics/README.md`
- `tests/test_docs_routes.py`

## Follow-Up Route

When a future route needs more operational detail, update the owning source
home, mechanic package, part contract, validator, release doc, or decision
record. Keep the root README as the route selector.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_nested_agents.py
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_docs_routes.py tests/test_design_surfaces.py
```
