# Keep Route Callers Distinct from Providers

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0086
- Original date: 2026-07-26
- Surface classes: route law, model contract, owner projection, agent identity
- SDK facets: control-plane, public interface, facade boundary
- Mechanic parents: boundary-bridge
- Guard families: owner provenance, agent identity, no synthesis, versioned behavior
- Posture: accepted

## Context

The live C1-to-C2 G8 chain showed that resolver v2 copied
`RouteIntent.requested_by` into every `RouteCandidate.agent`. The intent field
identifies the caller that requested navigation. The candidate field had been
treated by the R2 chain validator as a selected provider or scenario
participant.

C1 reads an `aoa-skills` capability graph but no exact `aoa-agents` provider
projection for those skill candidates. Copying the caller therefore created a
synthetic provider identity. C2 could ignore it, but the false metadata would
remain in the public route decision and every downstream evidence chain.

## Decision

Introduce `aoa_control_plane_route_resolver_v3`.

- Preserve all v2 scoring, challenger-health, constraint, ambiguity, and
  fail-closed behavior.
- Keep `RouteIntent.requested_by` solely as caller provenance.
- Emit `RouteCandidate.agent=None` until an exact stronger-owner provider
  projection is available.
- Resolve scenario participants separately from the admitted
  `aoa-playbooks` contour and pinned `aoa-agents` registry during C2 binding.
- Treat any future provider-agent population as a separately versioned route
  law that must name its owner projection and replay evidence.

## Rationale

Absence is more truthful than a convenient but false identity. The SDK may
correlate owner-qualified objects, but it cannot infer that the agent asking
for a route also provides the selected capability or belongs in the scenario
DAG.

## Consequences

- Positive: route decisions no longer misrepresent callers as providers.
- Positive: C1 entry navigation and C2 scenario composition have explicit,
  independent owner chains.
- Tradeoff: consumers that treated `RouteCandidate.agent` as the caller must
  read `RouteIntent.requested_by` instead.
- Tradeoff: resolver v2 trial receipts remain historical and a v3
  fresh-context replay is required.
- Stop line: `agent=None` does not mean agentless execution; it means C1 has
  not received authority to name a provider.

## Source Surfaces

- `src/aoa_sdk/control_plane/routing/resolver.py`
- `mechanics/boundary-bridge/parts/route-resolution-control-plane/`
- `src/aoa_sdk/contracts/control_plane.py`
- `src/aoa_sdk/control_plane/planning/bindings.py`

## Follow-Up Route

Replay one exact installed-wheel fresh-context route under v3, then verify the
three live C1-to-C2 scenario chains retain null entry-provider metadata and
owner-resolved scenario agents.

## Verification

Run the C1 focused suite, the installed-wheel route replay, and the public
three-scenario golden-chain verifier.
