# Experience Helper Contract Part Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0010
- Original date: 2026-05-31
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, artifact localization, Experience helpers, root technical districts, schema validation
- Mechanic parents: experience
- Guard families: mechanics topology, part validation, schema validation
- Posture: accepted

## Context

After the first Experience capture/pipeline move, root technical districts still
carried the main Experience helper contract families: adoption and federation
docs, deployment and watchtower docs, governance runtime docs, office/release
train docs, schemas, examples, and seed contract tests.

Those files were single-mechanic helper payloads. Their active root names made
the topology flatter than the actual operation map: an agent could see a wave
test or an API doc, but not the owner route, part role, next route, validation
home, or stop-line.

Sibling mechanics point to Experience as the shared parent, while SDK-local
helper bundles should live below it as parts. The active names therefore need
to say what the SDK owns: helper contracts, not adoption, governance,
deployment, or release authority.

## Decision

Localize the remaining Experience helper payload into functioning
`mechanics/experience/parts/` homes:

- `adoption-federation-helper-contracts`
- `deployment-watchtower-helper-contracts`
- `governance-runtime-helper-contracts`
- `office-release-train-helper-contracts`

Keep the already-localized `capture-pipeline-helper` as the capture route.

Move each family with its docs, schemas, examples, and tests. Rename active
tests away from wave labels toward route labels. Keep old root paths only in
provenance and migration ledgers.

## Rationale

The SDK helper topology should expose role, input, output, owner, next route,
and validation without forcing a future agent to reverse-engineer old root
files. These part names show the actual SDK operation and keep authority
outside `aoa-sdk`.

The split also avoids over-fragmenting the mechanic into tiny parts like
`adoption`, `rollback`, or `watchtower` when those files are actually coupled
helper-contract families with shared schema/example/test posture.

## Consequences

- Root `docs/`, `schemas/`, `examples/`, and `tests/` no longer own these
  Experience helper payloads.
- Active test names no longer use wave labels as their route identity.
- Schema `$id` values now point to part-local schema homes.
- `mechanics/experience/PARTS.md`, `PROVENANCE.md`, `AGENTS.md`,
  `mechanics/topology.json`, and `mechanics/ARTIFACT_TOPOLOGY.md` become the
  navigation surfaces for these helper bundles.
- Valid helper payloads remain contracts only; they do not authorize adoption,
  governance decisions, deployment, rollback, office activation, or release.

## Source Surfaces

- `mechanics/experience/README.md`
- `mechanics/experience/PARTS.md`
- `mechanics/experience/PROVENANCE.md`
- `mechanics/experience/parts/adoption-federation-helper-contracts/`
- `mechanics/experience/parts/deployment-watchtower-helper-contracts/`
- `mechanics/experience/parts/governance-runtime-helper-contracts/`
- `mechanics/experience/parts/office-release-train-helper-contracts/`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`

## Follow-Up Route

Continue the root technical district audit for remaining single-mechanic-owned
Recurrence, Titan, checkpoint, and boundary payloads.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
