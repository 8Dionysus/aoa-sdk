# AGENTS.md

## Applies to

This card applies to `aoa-sdk/kag/` and every nested path until a nearer card
narrows the lane.

## Role

`kag/` is the local KAG provider home for `aoa-sdk`. It exposes compact,
source-linked records over `SDK source home and typed KAG helper route` for `aoa-kag` registry,
composition, and MCP consumers.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `AGENTS.md`, `kag/README.md`, `kag/manifest.json`, `sdk/source_home.manifest.json`, `sdk/README.md`.

## Boundaries

Keep authored meaning with `aoa-sdk` source surfaces. Keep shared KAG schema,
registry, composition, and provider validation with `aoa-kag`. Keep runtime
serving state with `abyss-stack` or the runtime owner named by the consumer.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

Owner-local validation notes:

Use the owner validator named in `manifest.json`, then validate this provider
through the `aoa-kag` local subtree validator.

## Closeout

Report provider records changed, source-return route changed, owner validation,
`aoa-kag` validation, and the next MCP consumer route.
