# Responsibility routing without native interception

## Status

Accepted. Supersedes the universal pre-tool and phase-only reclassification
rules in [AOA-SDK-D-0100](AOA-SDK-D-0100-pre-tool-agent-routing-owner.md).

## Index Metadata

- Decision ID: AOA-SDK-D-0107
- Original date: 2026-09-07
- Surface classes: route law, model contract, skill exposure, agent boundary
- SDK facets: control-plane, public interface, validation
- Mechanic parents: boundary-bridge
- Guard families: owner provenance, goal binding, responsibility continuity
- Posture: accepted

## Context

The pre-tool route made native Codex helpers traverse an SDK intent, an
aoa-agents negative classification, and an aoa-summon compatibility packet.
It also invalidated responsibility classification solely because a session
resumed. Neither condition establishes an independent AoA duty. Shortening the
skill without changing these contracts would retain the same extra work.

## Options Considered

- Keep the universal gate and shorten only its prompt.
- Remove the external actor lifecycle and use native helpers for every duty.
- Keep independent responsibility with AoA and native orchestration with Codex.

## Decision

Choose the third option. `aoa-agents-skills` is the responsibility front door;
the SDK routing skill is retired from its owner port and managed OS profile.
Ordinary Codex helpers require neither an SDK call nor a negative receipt.

Keep `ControlPlaneAPI.pre_tool_route()` as a passive compatibility API. New
intents and decisions use v2; v1 inputs and decision records remain readable.
An absent or explicitly non-independent boundary returns `native_codex` with
no AoA next owner. This acknowledges the native route, not execution permission.

An explicit unresolved AoA boundary still returns to its meaning owner.
Independent responsibility remains on the external role-first route. Re-entry
with an existing obligation ref asks the owner to inspect that lifecycle,
without replacing its identity. Only an explicitly changed responsibility
requires a new unresolved boundary; the session phase alone does not.

## Rationale

The SDK can preserve typed owner references without becoming a second Codex
scheduler. AoA responsibility is an additional domain capability, not a toll
on every native tool. Current authority, runtime identity, and return checks
remain with their owners at the actual execution boundary.

## Consequences

- A native decision does not override Codex's permissions or delegation rules.
- Reused references do not prove currentness, runtime continuation, or acceptance.
- Legacy adapters must understand v2 decisions before opting into this route;
  no universal interception hook is installed by this change.
- External process/session, mandate, incarnation, and return evidence remain
  required by their owners. The SDK does not implement wake or Goal mutation.

## Source Surfaces

- `src/aoa_sdk/contracts/agent_tool_routing.py`
- `src/aoa_sdk/control_plane/agent_tool_routing.py`
- `skills/port.manifest.json`
- `skills/README.md`
- `mechanics/boundary-bridge/parts/route-resolution-control-plane/tests/test_agent_tool_routing.py`

## Follow-Up Route

`aoa-agents` owns the role-first skill and lifecycle procedures. `aoa-skills`
owns managed installation. Runtime adapters remain with `abyss-stack` and
Codex; absence of a supported lifecycle interface is an explicit integration gap.

## Verification

Use the route-resolution part's `VALIDATION.md` and the decision-index route.
Native, explicit-duty, unchanged-reentry, and changed-duty contract tests do
not prove model usefulness, an external launch, or a successful wake.
