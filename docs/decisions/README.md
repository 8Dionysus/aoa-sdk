# Decision Records Index

This directory is the durable decision surface for `aoa-sdk`.

Use it when a future contributor needs the rationale for a route, topology,
owner split, validator route, workflow boundary, compatibility posture,
control-plane API boundary, or SDK source/mechanic split.

Ordinary implementation notes, generated output, runtime logs, private
evidence, proof verdicts, memory objects, and one-off planning thoughts route
to their owning surfaces instead.

## Operating Card

| Field | Route |
| --- | --- |
| role | durable decision rationale entrypoint and index chooser |
| input | changed SDK source surface, owner boundary, rejected option, validation guard, or cross-surface route pressure |
| output | canonical decision note, generated lookup indexes, and route back to the source surface |
| owner | `docs/decisions/AGENTS.md` for lane law; decision notes for rationale; generated indexes for lookup only |
| next route | source surface first, then nearest route card, `docs/boundaries.md`, `ROADMAP.md`, generated lookup indexes, or the affected sibling owner |
| validation | `python scripts/generate_decision_indexes.py --check` plus the owning validator for the changed surface |

## Authority

Decision notes explain why a route was chosen.

They are weaker than the source surface they describe:

- SDK source and importable API meaning stay in `src/aoa_sdk/`;
- root route law stays in `AGENTS.md`;
- owner boundaries stay in `docs/boundaries.md`;
- direction stays in `ROADMAP.md`;
- generated companions stay derived from builders and source surfaces;
- sibling repositories keep their stronger truth for skills, techniques,
  evals, memo, agents, routing, playbooks, stats, KAG, and runtime behavior.

Generated decision indexes are weaker than the decision notes. They exist to
make lookup cheaper for agents, not to carry decision rationale.

## Index Shape

Each decision owns:

- a canonical `Decision ID: AOA-SDK-D-####`;
- a full canonical-ID filename, for example `AOA-SDK-D-0001-*.md`;
- an `## Index Metadata` block naming original date, surface classes, SDK
  facets, mechanic parents, guard families, and posture.

The lookup indexes under [indexes](indexes/README.md) are generated from that
metadata:

- [Decisions by canonical ID and number](indexes/by-number.md)
- [Decisions by date](indexes/by-date.md)
- [Decisions by surface class](indexes/by-surface.md)
- [Decisions by SDK facet](indexes/by-sdk-facet.md)
- [Decisions by mechanic parent](indexes/by-mechanic.md)
- [Decisions by validation or guard family](indexes/by-guard.md)

Regenerate the read models after decision metadata changes:

```bash
python scripts/generate_decision_indexes.py
```

Check generated parity before closeout:

```bash
python scripts/generate_decision_indexes.py --check
```

## Active Mechanics Decision

The corrected mechanics topology is recorded in
`AOA-SDK-D-0005-mechanics-parent-boundary-correction.md`. It supersedes the
first inventory-based skeleton's parent package set while preserving the same
route-only rule: no source payload moved into `mechanics/`.

## Addressing

Full canonical-ID decision paths are the active source files:

- `docs/decisions/AOA-SDK-D-0001-*.md`
- `docs/decisions/AOA-SDK-D-0002-*.md`
- `docs/decisions/AOA-SDK-D-####-*.md`

Canonical IDs remain stable handles. Previous path names belong to git, PR, or
release history, not to a compatibility lookup layer.

## Naming

Use the full canonical decision ID as the filename prefix:

`AOA-SDK-D-0001-short-decision-slug.md`

Prefer short titles that name the route, not the whole debate.

## Template

Start from [TEMPLATE.md](TEMPLATE.md) for new decisions. Keep notes concise,
but include enough context, options, rationale, consequences, source surfaces,
and validation for a future agent to avoid repeating the same route question.
