---
name: aoa-agent-tool-routing
description: Route an explicit agent, delegation, collaboration, sub-agent, or external-actor decision through the SDK-owned typed responsibility boundary before any built-in Codex agent tool. Use again after compaction, resume, re-entry, or a material plan change. Do not use for ordinary prose, keyword matches, model selection, runtime selection, or generic task decomposition; this front door is advisory and does not launch or enforce a hidden hook.
---

# SDK agent-tool routing

## Trigger

Use this front door when the current holder is about to make an actual agent
tool decision: delegate, collaborate, form a sub-agent, summon an actor, or
continue an independently owned duty. Use it again after compaction, resume,
re-entry, or a material plan change. A phrase that merely contains “agent” or
“delegate” is not a route trigger.

## Route procedure

1. Preserve the exact Goal, current responsibility holder, and `route_anchor`.
   The anchor must equal the Goal object id. Record whether an agent tool is
   actually requested and set the phase (`initial` or the relevant re-entry
   phase).
2. Present a typed `aoa_agent_tool_routing_intent_v1` to the SDK control plane
   through `ControlPlaneAPI.pre_tool_route()`; do not infer responsibility from
   keywords or choose a model, runtime, transport, or tool in this step.
3. For `awaiting_classification`, hand the unresolved boundary to
   `aoa-agents-skills`. The built-in Codex agent tool remains blocked.
4. For `owner_route`, hand the owner result to the `aoa-agents-skills`
   role-first entry. Independent responsibility must use the separately
   addressable external actor route; this front door does not launch it.
5. For `compatibility_local`, pass the exact
   `responsibility-classification-v1` result to `aoa-summon`. A built-in local
   child is deferred until that owner leaf admits the complete request.
6. For a non-agent decision, continue the current work without an agent tool.

## Re-entry law

After compaction, resume, re-entry, or material plan change, submit a fresh
unresolved intent. Never reuse a prior classification merely because its text
remains in context. The SDK decision's `must_reclassify` field is the typed
proof of this route obligation.

## Boundary

This skill is a model-visible route guide, not a universal runtime hook, daemon,
keyword rail, or enforcement layer. The SDK owns next-owner routing; it does
not own agent meaning, obligation formation, role selection, model fit,
transport, runtime activation, execution, return, or wake. Those boundaries
remain with `aoa-agents`, `aoa-summon`, `aoa-models`, and `abyss-stack`.

## Return

Return the typed SDK decision, the exact owner result or blocked reason, the
next owner route, and the stop line. A green route decision is not proof that a
classifier ran, an actor launched, work completed, or a master accepted the
return.
