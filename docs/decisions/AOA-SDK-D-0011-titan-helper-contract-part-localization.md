# Titan Helper Contract Part Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0011
- Original date: 2026-05-31
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, artifact localization, Titan helpers, root technical districts, CLI helper scripts
- Mechanic parents: titan
- Guard families: mechanics topology, part validation, schema validation, script smoke
- Posture: accepted

## Context

The Titan mechanic still carried its active helper payload in root technical
districts: `docs/TITAN_*.md`, `schemas/titan_*.schema.json`,
`examples/titan_*`, `scripts/titan*.py`, and `tests/test_titan_*.py`.

Those files are not repo-wide root contracts. They are SDK-owned helper
contracts around Titan runtime receipts, incarnation posture, console state,
appserver bridge replay, memory/recall candidates, visible-session replay, and
swarm closeout ledgers.

Sibling topology keeps `titan` as a real parent mechanic, while role authority,
memory truth, proof verdicts, and live runtime authority remain with stronger
owners. Therefore the SDK should keep Titan as a parent but place each helper
family under an active part route.

## Decision

Localize Titan root payload into functioning `mechanics/titan/parts/` homes:

- `incarnation-identity-runtime-helper-contracts`
- `operator-console-helper-contracts`
- `appserver-bridge-helper-contracts`
- `memory-loom-recall-helper-contracts`
- `session-praxis-replay-helper-contracts`
- `swarm-ledger-closeout-helper-contracts`

Move each family with its docs, schemas, examples, scripts, and tests. Keep
`src/aoa_sdk/titans/` as the importable SDK implementation package.

## Rationale

Active paths should show the operation map directly: role, input, output,
owner, next route, validation, and stop-line. Root script or doc names such as
`scripts/titanctl.py` and `docs/TITAN_MEMORY_LOOM.md` describe file shape, not
the mechanic route.

Using `*-helper-contracts` names makes the SDK boundary explicit. It validates
helper shape and local scripts without claiming Titan runtime, operator, role,
memory, proof, or owner authority.

## Consequences

- Root `docs/`, `schemas/`, `examples/`, `scripts/`, and `tests/` no longer
  own active Titan helper payloads.
- Part-local scripts locate the repository root by searching for
  `src/aoa_sdk`, so they remain executable from their active homes.
- Schema `$id` values now point to part-local schema homes.
- Old root paths remain provenance only.
- Titan helper validity remains weaker than live runtime state, operator
  approval, durable memory, proof verdicts, and owner truth.

## Source Surfaces

- `src/aoa_sdk/titans/`
- `mechanics/titan/README.md`
- `mechanics/titan/PARTS.md`
- `mechanics/titan/PROVENANCE.md`
- `mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/`
- `mechanics/titan/parts/operator-console-helper-contracts/`
- `mechanics/titan/parts/appserver-bridge-helper-contracts/`
- `mechanics/titan/parts/memory-loom-recall-helper-contracts/`
- `mechanics/titan/parts/session-praxis-replay-helper-contracts/`
- `mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`

## Follow-Up Route

Continue the root technical district audit for recurrence, checkpoint,
boundary-bridge, release-support, RPG, and antifragility payloads.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
