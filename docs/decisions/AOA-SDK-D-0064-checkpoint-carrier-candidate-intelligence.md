# Checkpoint Carrier Candidate Intelligence

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0064
- Original date: 2026-06-04
- Surface classes: checkpoint, classifier, generated-index, ecosystem-carrier, validation
- SDK facets: checkpoint control-plane, carrier intelligence, CLI facade, source topology
- Mechanic parents: checkpoint
- Guard families: owner boundary, no hidden automation, generated navigation, review gate
- Posture: accepted

## Context

AOA-SDK-D-0063 added checkpoint candidate intelligence below legacy
`candidate_kind`. That layer is useful for action events, action signatures,
repetition clusters, wrapper readiness, and wrapper-gap review.

It is not enough for the wider question the operator raised: mechanics are not
only SDK mechanics, and a repeated action may need a mechanic, tool, MCP access
plane, hook, script, service, daemon, or generated index carrier. Treating
`sdk_mechanic` as a wrapper family risked making a local checkpoint-control
case look like the AoA-wide mechanics ontology.

Sibling archaeology showed the stable meta-form:

- `Agents-of-Abyss` keeps mechanics as center route/topology packages with
  owner splits and owner-request gates.
- `aoa-memo` keeps mechanics operation-first and exposes generated owner-route
  matrices without claiming owner acceptance.
- `aoa-evals` separates proof mechanics, owner-local append tools, artifact
  verdict hook metadata, and MCP access-plane contracts.
- `aoa-agents` keeps specialization eligibility as a gate, not an install or
  projection action.
- `aoa-techniques` keeps mechanics as candidate movement around technique canon
  until atomic move, execution profile, owner boundary, and risk are named.
- `aoa-playbooks` separates scenario method from skill, proof, memory, routing,
  runtime, and scheduling authority.

Official MCP docs reinforce the split: MCP tools are schema-defined callable
interfaces exposed by servers, and applications should keep human oversight and
security controls for tool invocation. MCP is therefore an access-plane/service
boundary, not a synonym for any local callable helper.

## Decision

Add a second checkpoint navigation layer:

```text
action_signature -> wrapper_candidate -> carrier_candidate -> owner_scope -> review/install/execution gate
```

The SDK records `CarrierCandidate`, `ExistingCarrierFit`, `CarrierReadiness`,
`CarrierIntelligenceSample`, and `CarrierIntelligenceReport`.

Carrier kinds are:

- `mechanic` for route/topology/operation candidates;
- `tool` for callable operation candidates;
- `mcp` for external capability or access-plane candidates;
- `hook` for event-triggered automation candidates;
- `script`, `daemon`, `service`, and `index` only when evidence explicitly
  requires that carrier shape;
- `unknown` when the action shape is still too thin.

Owner scopes are `center`, `owner_repo`, `cross_repo`, `sdk_local`, and
`unknown`. `sdk_local` is a private SDK-local scope, not the head pattern for
mechanics.

Execution posture records whether the candidate is descriptive only, manual
only, review-required, install-blocked, or callable-blocked. The carrier layer
can produce review samples with accept, reject, weaken, split, or add-rule
lanes, but those verdict lanes remain unreviewed route evidence until an owner
acts.

`aoa checkpoint carrier-intelligence` reports the layer and, with
`--write-index`, writes:

```text
.aoa/session-growth/indexes/checkpoint-carrier-candidate-intelligence.min.json
```

The generated index groups by carrier kind, owner scope, execution risk,
installability, existing fit, cross-repo pressure, source wrapper family, sample
audit targets, and graph-ready anchors.

## Rationale

Wrapper classification and carrier classification answer different questions.

The wrapper layer asks whether an action looks like a skill, playbook,
technique, eval, memo route, owner-local wrapper, SDK-local checkpoint mechanic,
or unknown gap.

The carrier layer asks what kind of ecosystem carrier could safely hold the
repeated action if review agrees: route/topology mechanic, callable tool, MCP
access plane, event hook, script, service, daemon, or generated index.

Keeping those axes separate prevents a local SDK compatibility case from
becoming AoA mechanics truth. It also lets future RAG or GraphRAG work consume a
compact route index without letting generated navigation become memory, proof,
retrieval authority, or automation.

## Consequences

- Candidate intelligence can now expose carrier pressure without accepting a
  wrapper or owner verdict.
- Non-SDK mechanics such as memo writeback, eval proof routes, agent projection
  gates, technique adoption gates, and playbook scenario composition stay
  owner-scoped.
- Tools, MCP services, hooks, daemons, and services are blocked from implicit
  install/register/execute behavior.
- Single-event unknown pressure remains candidate-only and cannot become
  draftable.
- Sibling resemblance cannot force a candidate into `sdk_local`.

## Source Surfaces

- `src/aoa_sdk/checkpoints/carrier_intelligence.py`
- `src/aoa_sdk/checkpoints/carrier_indexes.py`
- `src/aoa_sdk/checkpoints/candidate_intelligence.py`
- `src/aoa_sdk/checkpoints/registry.py`
- `src/aoa_sdk/contracts/checkpoints.py`
- `src/aoa_sdk/cli/checkpoint.py`
- `src/aoa_sdk/cli/rendering.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_carrier_intelligence.py`
- `mechanics/checkpoint/README.md`
- `mechanics/checkpoint/ROADMAP.md`

## Follow-Up Route

Use carrier samples to tune classifier rules only after reviewing sibling-shaped
evidence. Do not auto-create mechanics, install hooks, register MCP services,
execute tools, start daemons, write owner memory, prove invariants, or claim
RAG/GraphRAG authority from this index.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
