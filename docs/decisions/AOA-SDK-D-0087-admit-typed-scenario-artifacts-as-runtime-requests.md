# Admit Typed Scenario Artifacts as Runtime Requests

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0087
- Original date: 2026-07-26
- Surface classes: public API, runtime boundary, adapter protocol, integration
- SDK facets: control-plane, public interface, runtime entry
- Mechanic parents: runtime-seam, boundary-bridge
- Guard families: exact binding, owner provenance, no execution, typed scenario input
- Posture: accepted

## Context

The first `AbyssStackRuntimeBinding` supported
`bounded_change_safe` by requiring `request_ref` to appear in
`ScenarioBinding.input_refs`. The other admitted golden contours use
`input_artifact_bindings` because `summon_request`, `summon_decision`,
`child_task_result`, and `owner_runtime_receipt` have typed roles in the
owner-authored playbook plan.

Copying one of those refs into the untyped list would erase its role and create
two representations of the same input. Widening the binding to accept any
snapshot source would be worse: it would let a policy, generated projection,
or unrelated owner artifact become the executable runtime request.

## Options Considered

- Duplicate the primary typed artifact in `ScenarioBinding.input_refs`.
- Add a second binding schema and field for typed requests.
- Accept any source ref present in the plan snapshot.
- Keep one binding field and admit only exact untyped or typed scenario input
  refs that are also bound to an active plan step.

## Decision

Keep `abyss_stack_agent_os_binding_v1` and its single `request_ref`.

`assert_abyss_stack_binding_matches_plan()` admits that ref only when it is:

- present in `ScenarioBinding.input_refs`, or
- the exact `artifact_ref` of one `ScenarioArtifactBinding`;

and in both cases it must appear in at least one active `RunPlan` step input,
have one exact absolute delivery coordinate, and remain covered by the full
source/ABI snapshot map.

The runtime-owner compatibility profile decides which admitted input is the
primary request for a scenario. The SDK does not select an artifact kind,
interpret its payload, or infer runtime behavior.

## Rationale

The additive rule preserves the stable binding ABI while retaining typed
scenario meaning and exact owner provenance. Requiring active-step use keeps a
mere snapshot dependency from becoming runtime authority. Payload admission
and execution semantics remain with `abyss-stack`.

## Consequences

- Positive: A2A and degradation plans can use their authored typed inputs
  without compatibility duplication.
- Positive: existing bounded-change callers and serialized bindings remain
  unchanged.
- Tradeoff: the runtime profile must still name one primary typed input and
  reject ambiguous or unsupported contours.
- Stop line: typed request admission is transport binding, not capability
  activation or model/tool execution.

## Source Surfaces

- `src/aoa_sdk/runtime_adapters/abyss_stack.py`
- `mechanics/runtime-seam/parts/abyss-stack-runtime-adapter/`
- `src/aoa_sdk/contracts/control_plane.py`
- `repo:abyss-stack/docs/decisions/ABYSS-STACK-D-0089-owner-bound-agent-os-execution-lanes.md`

## Follow-Up Route

Keep installed-wheel paired tests for untyped bounded change, typed A2A
return, and typed degradation recovery. A future transport field or binding
schema requires a separate versioned decision.

## Verification

Run the focused SDK runtime-adapter suite, full SDK tests, source-topology
checks, build/release gates, and the paired `abyss-stack` production adapter
suite against the installed wheel.
