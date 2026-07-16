# Skill Evidence Requires an Explicit Owner

## Status

Accepted.

This decision supersedes the SDK-owned skill trigger and usage-gap producer
branch in AOA-SDK-D-0058. It does not remove the generic recurrence transport
for an explicitly authored owner observation.

## Index Metadata

- Decision ID: AOA-SDK-D-0069
- Original date: 2026-07-15
- Surface classes: recurrence, owner boundary, compatibility, validation
- SDK facets: live observations, hook bindings, skill evidence transport
- Mechanic parents: recurrence, boundary-bridge
- Guard families: owner authority, no inferred execution, manual evidence, no silent no-op
- Posture: accepted

## Context

The former `aoa-skills` topology published description-trigger cases,
activation beacons, live skill receipts, and recurrence hook manifests. The SDK
compared positive trigger cases with receipt names and emitted an inferred
usage gap when no matching name appeared.

AOA-SK-D-0039 replaced that topology with a semantic capability tree, typed
relations, seven focused bundles, manual lifecycle comparison, and task-local
runtime DAGs. It removed the trigger-eval, activation-beacon, recurrence, and
receipt surfaces from the active owner checkout. Session evidence may suggest
a candidate, but absence of a receipt is not proof that a skill should have
run or that it improved the result.

A manual SDK run against the clean current `aoa-skills` owner found no skill
recurrence component and no supported trigger inputs. Nevertheless,
`list_live_producers()` still advertised `skill_trigger_surface_watch`; running
it returned an empty packet without a warning. That is a false-green
connectivity claim, not useful compatibility behavior.

## Options Considered

- Recreate the removed trigger and receipt surfaces as SDK fixtures.
- Retain the producer as an optional no-op for old workspaces.
- Remove SDK-owned skill-use inference and accept only explicit owner-authored
  evidence through generic reviewed transport.

## Decision

Choose the third option.

- Remove `skill_trigger_surface_watch`, `skill_trigger_gap_watch`, the default
  `component:skills:bundle-and-activation-beacons` mapping, and their active
  examples, schemas, and fixtures.
- Do not infer selection, execution, omission, benefit, collision, or lifecycle
  state from description similarity, a positive trigger case, or receipt
  absence.
- Keep prompt visibility, routing recommendation, host selection, skill-body
  loading, execution, and outcome effect as distinct evidence states. A skill
  mention or loaded `SKILL.md` alone proves neither invocation nor benefit.
- Keep raw task traces, task-local DAGs, host selection behavior, and session
  usage evidence with the executing session and its session-memory owner.
- Route reusable skill-effect evaluation to the skill and eval owners, where
  no-skill, current, candidate, negative, coexistence, and held-out manual
  comparisons can establish an explicit result.
- The recurrence control plane may still validate and carry a future
  owner-authored skill observation or beacon through its generic typed
  contracts. It may not manufacture that observation from retired inputs.
- Legacy workspaces remain inspectable through Git and owner provenance; the
  SDK does not preserve executable compatibility with the retired producer.

## Rationale

The old inference conflated applicability expectations, host selection,
execution evidence, and outcome benefit. It also treated missing session data
as a negative observation. Removing the producer makes absence honest and
keeps the SDK subordinate to both the skill owner and the executing runtime.

Generic transport remains useful because a future owner may deliberately
publish a reviewed observation under a current contract. Requiring that
explicit source avoids turning the SDK into a hidden skill evaluator.

## Consequences

- The live producer list and hook producer enum become smaller.
- Old hook manifests using `skill_trigger_gap_watch` are unsupported and must
  be migrated or retained only as historical evidence by their owner.
- Active recurrence examples no longer teach the retired activation-beacon
  component as current owner truth.
- Skill-use investigation becomes more evidence-intensive but no longer gains
  false confidence from missing receipts.

## Source Surfaces

- `src/aoa_sdk/recurrence/live_observations.py`
- `src/aoa_sdk/recurrence/hooks.py`
- `src/aoa_sdk/recurrence/contracts/base.py`
- `mechanics/recurrence/parts/live-observation-producers/`
- `mechanics/recurrence/parts/hook-observation-pack/`
- `mechanics/recurrence/parts/component-manifest-gate/`
- `mechanics/recurrence/parts/graph-closure-snapshot/`
- `mechanics/recurrence/parts/downstream-projection-guard/`
- `mechanics/recurrence/parts/review-decision-closure/`
- `docs/decisions/AOA-SDK-D-0067-owner-scoped-skill-inspection.md`

## Follow-Up Route

Route session-local usage lookup to `aoa-session-memory`, skill lifecycle and
procedure truth to `aoa-skills` or the repository home owner, comparative proof
to `aoa-evals`, retrieval to `aoa-kag`, and execution to the host runtime.

Treat hook-manifest format compatibility as a separate registry concern; do
not conceal an incompatible foreign manifest by restoring this producer.

## Verification

- manual current-owner run proving the retired producer has no admitted inputs;
- manual absence check for old skill producer names and default components;
- manual generic recurrence run proving unrelated producers still work;
- focused tests retained only for the resulting producer-list, hook-contract,
  and owner-boundary invariants;
- decision indexes, source topology, recurrence mechanics, and full repository
  gates before landing.
