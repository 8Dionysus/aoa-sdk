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
fit-query result and projection. Historical v1 bindings remain readable, but
do not satisfy the v2 evidence requirement for a new actor route.

See [CONTRACT.md](CONTRACT.md) and [VALIDATION.md](VALIDATION.md).
