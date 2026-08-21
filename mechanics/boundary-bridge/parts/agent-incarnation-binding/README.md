# Agent Incarnation Binding

This part owns the SDK-visible, runtime-neutral binding between one exact task
request, one `aoa-agents` role contract, one `aoa-models` realization, one
runtime-owner profile, one workspace source, and one immutable `RunPlan`.

The binding is post-compile: C2 still emits no model choice, prompt, tool
argument, or MCP binding. The caller supplies exact owner-qualified refs, and
the SDK validates that they remain inside the plan snapshot and scenario.

The SDK also exposes an owner-subordinate loader for the exact
`abyss-stack` external-Codex runtime descriptor. It projects runtime
compatibility and provenance into `RuntimeProfile`; it does not inspect the
descriptor to choose a model, effort, role, or tool profile.

The included continuation obligation carries the state needed after a parent
inference truly yields. Its wake policy is event-filtered: child completion is
an event, not an automatic order to wake the parent.

`AgentIncarnationBindingV2` is the evidence-complete contract for new external
actors. It additionally binds the exact `aoa-agents` obligation, actor mandate,
and passive role-resolution result plus the content-addressed `aoa-models`
fit-query result and projection. It also carries the exact content-addressed
runtime subject selected by that query; the subject participates in the
binding digest so a mutable executable path cannot substitute package
identity. Historical v1 bindings remain readable, but do not satisfy the v2
evidence requirement for a new actor route.

`build_obligation_actor_run_plan` removes the task-local hand assembly that
previously sat between those already-made owner decisions and incarnation
binding. It accepts an exact task-local DAG, role, request, owner inputs,
runtime profile, ABI refs, effect class, outputs, and closeout owners. It emits
one runtime-neutral `RunPlan`; it does not infer any missing choice and admits
only bounded read-only or repository-local mutation effects.

See [CONTRACT.md](CONTRACT.md) and [VALIDATION.md](VALIDATION.md).
