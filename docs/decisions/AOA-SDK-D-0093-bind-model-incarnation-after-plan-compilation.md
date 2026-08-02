# Bind model incarnation after plan compilation

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0093
- Original date: 2026-08-01
- Surface classes: public API, model contract, runtime boundary, continuation
- SDK facets: control-plane, plan compilation, runtime entry, lifecycle
- Mechanic parents: boundary-bridge, runtime-seam
- Guard families: owner provenance, exact binding, no execution, effect ceiling, re-entry
- Posture: accepted

## Context

C2 intentionally emits no model choice, prompt, tool argument, or MCP binding.
C3 prepares and coordinates a `RunPlan` through a caller-supplied runtime
adapter. An external persistent Codex agent nevertheless needs one exact,
reviewable connection among the task request, role, model realization,
runtime/tool profile, workspace source, permissions, usage metering, continuation, and
wake policy before the runtime can launch it.

Putting a model slug into role truth would equate a durable role with a
temporary embodiment. Putting it into C2 would make the plan compiler select
model meaning owned by `aoa-models`. Letting a runtime infer the binding would
hide the parent obligation and effect ceiling from the control plane.

## Options Considered

- Add model fields directly to `aoa-agents` roles or summon requests.
- Add model choice directly to `RunPlan` and C2 compilation.
- Let each runtime infer role/model/tool binding from a free-form request.
- Introduce one separate post-compile SDK binding of exact owner refs.

## Decision

Add `aoa_agent_incarnation_binding_v1` as a post-compile, runtime-neutral
control-plane contract. `AgentIncarnationBinding` references rather than
copies the exact task request, role contract, `aoa-models` realization,
runtime and tool profile, workspace source, result schema, and `RunPlan`.

It also carries an explicit permission ceiling, observe-only usage metering,
semantic stop conditions, and a complete
continuation obligation and event-filtered wake policy. The SDK hashes and
validates the binding against the exact plan. It does not select the model,
interpret fit claims, launch a process, poll with inference, issue proof, or
grant acceptance.

Usage metering has no token, time, turn, output, or cost ceiling. Those values
are observations for later `aoa-stats`/`aoa-evals` interpretation, not a reason
for the SDK or runtime to truncate agent initiative. Provider-enforced limits
and explicit operator interruption are recorded as runtime facts.

## Rationale

The separate binding protects the accepted model-neutral C2 boundary while
making the otherwise hidden incarnation decision inspectable before C3/C4
runtime entry. It also gives true yield/re-entry a durable object without
turning the first parent/child compatibility vocabulary into a final A2A
ontology.

## Consequences

- Existing `RunPlan` bytes and compiler semantics remain unchanged.
- Runtime owners receive one exact binding instead of inferring model, tools,
  permissions, or wake behavior from prose.
- The cross-object gate revalidates the plan snapshot and canonical plan
  digest; a binding cannot bless changed plan bytes that retain an old digest.
- A runtime-owner descriptor loader may project the exact external-Codex
  compatibility profile into `RuntimeProfile`, but it does not select among
  that descriptor's model or tool entries.
- A caller must provide more owner-qualified refs and cannot rely on implicit
  user configuration.
- Model realization meaning remains in `aoa-models`; role meaning remains in
  `aoa-agents`; execution and session identity remain in the runtime owner.
- A valid binding is still only a candidate for runtime admission.

## Source Surfaces

- `src/aoa_sdk/contracts/incarnation.py`
- `src/aoa_sdk/control_plane/incarnation.py`
- `src/aoa_sdk/runtime_adapters/abyss_stack.py`
- `mechanics/boundary-bridge/parts/agent-incarnation-binding/`
- `docs/boundaries.md`

## Follow-Up Route

Carry the exact binding through the explicit `abyss-stack` runtime adapter and
prove it with a separate Codex/Luna process, durable session, structured
result, independent review, and event-filtered return. Keep external effects
disabled until separately approved.

## Verification

Run the part-local schema, unit, lint, type, topology, and source-home checks,
then pair them with runtime-owner execution tests. SDK-only validation cannot
prove a model process ran or produced net benefit.
