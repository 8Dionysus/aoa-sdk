# Decision Index Read Model Symmetry

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0066
- Original date: 2026-06-04
- Surface classes: docs, generated-index, route-law, validation
- SDK facets: decision lane, generated navigation, control-plane
- Mechanic parents: none
- Guard families: decision drift, generated navigation, route clarity
- Posture: accepted

## Context

The SDK decision lane already used canonical `AOA-SDK-D-####` filenames,
metadata-backed generated indexes, and an index contract. Its generated lookup
tables still diverged from the newer sibling pattern: `by-number.md` folded the
canonical ID into the link text and omitted an explicit path column, while
date and grouped indexes repeated full metadata tables at every group.

That shape was valid, but it made the SDK lookup surface heavier and less
symmetrical than the current decision-index read models used by neighboring
refactored repositories.

## Options Considered

- Keep the SDK index renderer unchanged because generated parity was already
  green.
- Copy a sibling generator wholesale.
- Keep the SDK-local generator but adopt the shared read-model shape: a
  canonical ledger in `by-number.md`, bullet lookup lists for date and grouped
  indexes, and explicit path coordinates for every lookup entry.

## Decision

Keep the SDK-local generator and change its rendered read models to the shared
decision-index lookup shape.

`by-number.md` is the complete canonical ledger and must expose separate
`Decision ID`, `Decision`, and `Path` columns. Date and grouped indexes are
lookup routes, not repeated ledgers, so they use bullet entries with canonical
link text and the source path.

## Rationale

The source truth is still each decision note and its `## Index Metadata` block.
The generated indexes should make lookup cheaper without becoming a second
metadata authority.

Keeping the generator local respects the SDK's existing validation surface.
Changing only the rendered read-model shape spreads the better sibling
navigation contract without importing sibling owner semantics into `aoa-sdk`.

## Consequences

- `by-number.md` becomes easier to scan as the canonical ledger.
- Date, surface, SDK facet, mechanic, and guard indexes become shorter lookup
  routes with stable source coordinates.
- Generated output changes broadly, but the source-of-truth boundary does not.
- Future SDK decision-index changes should preserve explicit canonical IDs and
  source paths.

## Source Surfaces

- `scripts/generate_decision_indexes.py`
- `docs/decisions/indexes/by-number.md`
- `docs/decisions/indexes/by-date.md`
- `docs/decisions/indexes/by-surface.md`
- `docs/decisions/indexes/by-sdk-facet.md`
- `docs/decisions/indexes/by-mechanic.md`
- `docs/decisions/indexes/by-guard.md`
- `tests/test_decision_indexes.py`

## Follow-Up Route

Use generated indexes for decision lookup. If the decision index contract
changes again, update the generator, focused tests, generated read models, and
decision-lane route card together.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python -m pytest -q tests/test_decision_indexes.py
```
