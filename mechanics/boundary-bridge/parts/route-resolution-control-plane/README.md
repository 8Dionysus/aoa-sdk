# Route Resolution Control Plane

## Role

This Boundary Bridge part implements C1 of the Agent OS control plane:
deterministic, explainable route-candidate selection from receipt-bound owner
projections. It does not activate a capability, compile a run plan, choose a
runtime, or execute an effect.

## Inputs

- a strict `RouteIntent`;
- the explicitly configured SDK-canonical routing runtime bundle;
- the packaged canonical routing source lock, or an explicit test/rehearsal
  override;
- the exact pinned `aoa-skills` capability graph commit named by that lock.

The loader verifies the G5 runtime manifest, canonical SDK producer, owner
switch receipt, stronger-owner trust admission, subject and file digests,
canonical paths, and owner projection bindings before any candidate is
eligible.

## Outputs

- a content-addressed `RouteDecision`;
- a `RouteExplanation` accounting for every candidate;
- explicit blocked or degraded states;
- `fallback_used=false`;
- source, graph, runtime mirror, and resolver provenance.

## Selection law

Version `aoa_control_plane_route_resolver_v3` uses only owner-authored
retrieval fields from the pinned capability graph:

| Signal | Score |
| --- | ---: |
| positive token | +40 |
| routing token | +20 |
| general token | +5 |
| negative token | -50 |
| exact negative phrase | -200 and forbidden |
| exact capability id or name | +1000 |
| explicit `required_capability` match | +2000 |

Scores are integers and candidate order is stable. An equal eligible top score
blocks the decision; lexical order is never used as a semantic tie-break.
Missing, duplicate, or inconsistent owner projections also block.

Only `skill` capabilities are resolvable in C1. Candidate-only, deferred, or
suggest-only capabilities require an exact `required_capability` constraint.
Unsupported policy constraints block instead of being guessed.

Owner health follows the complete `aoa-skills` enum. `healthy` is compatible,
`challenger` and `degraded` remain explicit degraded candidates, and missing,
unrecognized, unavailable, or retired health stays incompatible. Accepting an
advertised challenger does not promote it to healthy or turn selection into a
proof verdict.

`RouteIntent.requested_by` remains only the caller identity. C1 has no pinned
provider-agent projection for a skill candidate, so `RouteCandidate.agent` is
`None`; the resolver must not relabel the caller as a provider. Scenario agents
are resolved later from the exact admitted playbook contour.

## Public routes

- Python: `AoASDK.control_plane.resolve()` and
  `AoASDK.control_plane.explain()`;
- CLI: `aoa route resolve`, `aoa route explain`, and `aoa route validate`.

## Next route

C2 compilation now routes through
`mechanics/boundary-bridge/parts/plan-compilation-control-plane/`. C3 may add
`AoARunner` only behind runtime-adapter and lifecycle contracts. Neither slice
may reinterpret a C1 decision as activation authority.

## Validation

Use [VALIDATION.md](VALIDATION.md). Green C1 checks prove deterministic SDK
resolution over the tested snapshot; they do not prove capability invocation,
task success, cost reduction, runtime admission, or Agent OS benefit.

The bounded v2 fresh-context record remains in
[`trials/fresh-context-resolver-v2.json`](trials/fresh-context-resolver-v2.json)
as historical evidence for the challenger-health change. The current v3
caller/provider replay is retained separately in
[`trials/fresh-context-resolver-v3.json`](trials/fresh-context-resolver-v3.json).
