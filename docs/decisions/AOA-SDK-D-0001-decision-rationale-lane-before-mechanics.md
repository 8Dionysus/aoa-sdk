# Decision Rationale Lane Before Mechanics

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0001
- Original date: 2026-05-31
- Surface classes: root/topology, docs route, validation guard
- SDK facets: decision lane, control-plane, mechanics prep
- Mechanic parents: none
- Guard families: rationale route, index parity, source topology
- Posture: accepted

## Context

`aoa-sdk` is moving toward the same route-oriented topology used by the
refactored AoA repositories. The next structural pressure is to introduce
`mechanics/`, but that move needs a local rationale lane first.

Without `docs/decisions/`, the first mechanics landing would have no stable
place to record why a package is a shared AoA mechanic, why a package is a
local SDK mechanic, or why SDK source stays in `src/aoa_sdk/` instead of being
renamed by surface pressure.

Sibling repositories already use canonical decision IDs and generated lookup
indexes to keep rationale separate from active source surfaces. `aoa-sdk`
needs the same lane before it starts moving docs, schemas, examples, scripts,
or validators into mechanic-local homes.

## Options Considered

- Add `mechanics/` first and record rationale in the mechanic README.
- Keep rationale in root `README.md`, `AGENTS.md`, or `ROADMAP.md`.
- Add a canonical decision lane first, then use it for mechanics and SDK-source
  topology choices.

## Decision

Create `docs/decisions/` as the canonical rationale lane for `aoa-sdk` before
introducing `mechanics/`.

Decision records use full canonical `AOA-SDK-D-####` filenames and an
`Index Metadata` block. Generated indexes under `docs/decisions/indexes/`
are lookup read models produced by `scripts/generate_decision_indexes.py`.

## Rationale

The SDK is a control-plane consumer and helper layer. Its topology choices often
sit between imported sibling truth, local typed APIs, generated companions,
and future mechanics. Those choices need rationale that is durable but weaker
than the source surface being explained.

Putting the rationale lane first prevents mechanics work from becoming a
cosmetic folder migration. It also keeps root docs short: root route cards can
point to decisions, while source behavior remains in the owning SDK, docs,
schema, generated, or sibling surface.

## Consequences

- Structural SDK topology changes now have a local decision address.
- Generated decision indexes make lookup cheap without turning indexes into
  rationale authority.
- Future mechanics work should create or update a decision note when it changes
  owner split, top-level mechanic names, validator authority, or source-lane
  placement.
- The decision lane does not itself create `mechanics/` and does not decide
  whether a future mechanic is shared AoA vocabulary or local SDK vocabulary.

## Source Surfaces

- `AGENTS.md`
- `README.md`
- `ROADMAP.md`
- `docs/boundaries.md`
- `docs/decisions/AGENTS.md`
- `scripts/generate_decision_indexes.py`

## Follow-Up Route

Use this lane for the next decision that introduces `mechanics/` and names the
SDK rule for shared AoA mechanics versus justified local SDK mechanics.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_nested_agents.py
```
