# SDK Pre-Tool Agent Routing Owner

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0100
- Original date: 2026-08-15
- Surface classes: route law, model contract, owner projection, agent boundary
- SDK facets: control-plane, public interface, skill exposure, validation
- Mechanic parents: boundary-bridge
- Guard families: owner provenance, goal binding, re-entry freshness, no tool selection
- Posture: accepted

## Context

The installed `aoa-agents` owner skill correctly owns responsibility meaning
but is not a universal pre-tool hook. The merged interception change therefore
could not prove that an ordinary Codex agent-tool choice reached the owner
classifier before a built-in child tool. Re-entry after compaction, resume, or
plan change also needed an explicit freshness boundary.

The missing surface belongs to `aoa-sdk`: it owns the universal typed control
plane and route producer, while `aoa-agents` retains classification, obligation,
role, transfer, return, and wake meaning.

## Decision

Add `aoa_agent_tool_routing_intent_v1` and
`aoa_agent_tool_routing_decision_v1` to the SDK control plane and expose
`ControlPlaneAPI.pre_tool_route()`.

The SDK route:

- requires an explicit agent-tool decision, exact Goal/current-holder refs, and
  a route anchor equal to the Goal;
- sends an unresolved boundary to `aoa-agents-skills`;
- sends an owner-classified independent result back to the
  `aoa-agents-skills` role-first entry;
- sends an owner-classified `not_independent` result only to `aoa-summon` as a
  compatibility local leaf, with the built-in tool deferred until that leaf;
- forces a fresh unresolved classification after compaction, resume, re-entry,
  or material plan change; and
- does not select a model, transport, runtime, process, or tool, and does not
  implement a hidden hook or daemon.

The model-visible `aoa-agent-tool-routing` skill is an advisory front door for
this typed route. Global exposure is through `aoa-skills`'s single
`os-user-default` profile; no repository-local duplicate projection is added.

## Rationale

This keeps the universal route with the canonical control plane without
absorbing the agent owner's semantic authority. Typed state prevents keyword
rails from deciding responsibility, while explicit phase handling prevents a
stale classification from silently surviving re-entry.

## Consequences

- A green SDK route test proves typed next-owner posture, not owner
  classification, actor launch, runtime execution, or master acceptance.
- `aoa-agents` must still produce the exact owner result and enforce its own
  summon/obligation contracts.
- The installed profile and a fresh model-visible prompt check are required
  before claiming global route exposure.

## Source Surfaces

- `src/aoa_sdk/contracts/agent_tool_routing.py`
- `src/aoa_sdk/control_plane/agent_tool_routing.py`
- `src/aoa_sdk/control_plane/api.py`
- `skills/aoa-agent-tool-routing/SKILL.md`
- `skills/port.manifest.json`
- `mechanics/boundary-bridge/parts/route-resolution-control-plane/tests/test_agent_tool_routing.py`

## Follow-Up Route

Use the `aoa-agents` owner-local classifier for the returned boundary, then use
the admitted external actor/runtime route for independent responsibility.

## Verification

Run the focused typed route tests, SDK source/topology and decision-index
validators, install the single user profile, and perform a fresh external
actor execution with separate process/session/return evidence.
