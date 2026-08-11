# Bind obligation and fit evidence in incarnation v2

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0096
- Original date: 2026-08-10
- Surface classes: public API, model contract, runtime boundary, compatibility
- SDK facets: control-plane, runtime entry, incarnation binding
- Mechanic parents: boundary-bridge, runtime-seam
- Guard families: owner provenance, exact binding, model-fit evidence, compatibility
- Posture: accepted

## Context

The v1 incarnation binding tied a plan to one role contract, realization, and
runtime profile, but it did not preserve why the goal needed a separate actor,
which mandate the actor accepted, which exact role-source resolution supported
that mandate, or which current model-fit evidence informed the realization.
Those objects existed beside the binding in `aoa-agents-skills` and
`aoa-models`, so a runtime could receive a schema-valid incarnation while the
responsibility and fit chain remained implicit.

Adding optional fields to v1 would let new bindings omit the same evidence and
would silently change the meaning of historical receipts.

## Options Considered

- Keep obligation, mandate, and fit refs only in an outer runtime request.
- Add optional evidence refs to v1.
- Preserve v1 read compatibility and introduce a required evidence-complete v2
  contract for new external actors.

## Decision

Keep `AgentIncarnationBinding` and its v1 schema byte-compatible for historical
runtime receipts. Add `AgentIncarnationBindingV2` and a separate builder that
requires exact content refs for:

- the `aoa-agents` obligation;
- the `aoa-agents` actor mandate;
- the `aoa-agents` passive role resolution;
- the content-addressed `aoa-models` fit-query v2 result;
- the exact `aoa-models` fit projection beside the existing realization ref.

The v2 validator checks owner and schema identity and requires the realization
and projection to share one model-owner source ref. The builder still consumes
caller-selected refs, validates the unchanged `RunPlan`, computes one canonical
binding digest, and performs no model selection or execution.

## Rationale

New actor incarnations need a content-addressed chain from responsibility to
physical realization. A distinct v2 makes that chain mandatory without
rewriting the meaning of already preserved v1 evidence or forcing frozen
runtime receipts through a new schema.

## Consequences

- New external-actor routes can reject an incarnation that lacks obligation,
  mandate, role-resolution, or model-fit evidence.
- Historical v1 artifacts remain readable and their generated schema remains
  byte-identical.
- Runtime owners must explicitly admit v2 before using it for new launches;
  v1 compatibility does not satisfy the new actor route.
- Model-fit and role meaning remain with their source owners; SDK only binds
  exact refs.

## Source Surfaces

- `src/aoa_sdk/contracts/incarnation.py`
- `src/aoa_sdk/control_plane/incarnation.py`
- `mechanics/boundary-bridge/parts/agent-incarnation-binding/schemas/agent-incarnation-binding-v2.schema.json`
- `mechanics/boundary-bridge/parts/agent-incarnation-binding/tests/test_agent_incarnation_binding.py`

## Follow-Up Route

Require the v2 binding and exact fit result/projection refs in the
`aoa-agents` external summon packet, then add explicit v2 admission to the
`abyss-stack` runtime without weakening v1 receipt reading.

## Verification

Run v1/v2 schema parity, part-local tests, lint, mypy, mechanics topology,
source-home validation, and the repository release gate. Pair SDK proof with
runtime-owner integration; SDK checks do not prove process execution.
