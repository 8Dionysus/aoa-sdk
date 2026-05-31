# AGENTS.md

## Applies to

This card applies to `docs/decisions/` and the generated lookup indexes under
`docs/decisions/indexes/`.

## Role

`docs/decisions/` preserves durable rationale for SDK topology, ownership,
route-law, validation, compatibility, and workflow choices.

Decision records explain why a path was chosen. They do not replace active SDK
source, route cards, schemas, examples, generated companions, validators, or
sibling-owner truth.

## Boundaries

- Use canonical `AOA-SDK-D-####` filenames for active decision records.
- Keep decisions short, evidence-linked, and public-safe.
- Do not use decision notes for raw evidence, generated output, release notes,
  session transcripts, or routine implementation details.
- Generated indexes are lookup read models only. They are weaker than the
  source decision note and weaker than the active surface the decision
  describes.
- When a decision changes active behavior, update the source surface and its
  validator in the same slice.
- When a decision routes to a sibling owner, name the stop-line without
  importing that owner's authority into `aoa-sdk`.

## Index Metadata

Every decision record must include an `## Index Metadata` block with:

- `Decision ID: AOA-SDK-D-####`
- `Original date: YYYY-MM-DD`
- `Surface classes: ...`
- `SDK facets: ...`
- `Mechanic parents: ...`
- `Guard families: ...`
- `Posture: ...`

Use `none` only when a field is intentionally empty.

## Validation

For decision-lane changes, run:

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_nested_agents.py
```

For release-facing or broad topology changes, also run the root validation
route from `AGENTS.md`.
