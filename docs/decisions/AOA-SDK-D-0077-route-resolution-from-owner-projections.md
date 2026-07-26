# Resolve Agent OS Routes from Receipt-bound Owner Projections

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0077
- Original date: 2026-07-26
- Surface classes: public API, CLI, route law, owner projection, runtime boundary
- SDK facets: control-plane, public interface, facade boundary, runtime entry
- Mechanic parents: boundary-bridge
- Guard families: deterministic resolution, snapshot trust, owner binding, ambiguity, no activation
- Posture: accepted

## Context

The G5 succession made `aoa-sdk` the canonical routing producer and the live
runtime now consumes its receipt-bound artifact. R2 already defined strict
`RouteIntent`, `RouteDecision`, and `RouteExplanation` models, but the SDK had
no callable resolver. Agents still had to reproduce selection logic outside
the SDK, weakening provenance, consistency, and the intended Agent OS control
plane.

A resolver cannot treat the compact routing registry as capability truth.
Capability meaning, lifecycle, applicability, bindings, effects, and approval
posture remain owned by `aoa-skills`. It also cannot use lexical order or an
opaque model call to hide ambiguity.

## Options Considered

- Keep route selection in each executing agent.
- Rank directly from the SDK routing registry.
- Use a model-based semantic ranker with a lexical fallback.
- Resolve deterministically from the intersection of a trusted canonical
  routing snapshot and an exact pinned owner capability projection.

## Decision

Implement C1 as `aoa_control_plane_route_resolver_v1`.

`AoASDK.control_plane` must:

- require an explicitly configured SDK-canonical runtime bundle;
- verify the exact G5 manifest, receipt, trust admission, source lock, paths,
  refs, and digests before resolution;
- read the exact pinned `aoa-skills` capability graph through Git without
  requiring an `aoa-routing` checkout;
- form candidates only where routing registry and owner projection agree;
- score only versioned owner retrieval fields using the published integer
  score law;
- block equal eligible top scores, missing or mixed projections, unsupported
  capability kinds, and unsupported or conflicting constraints;
- require an exact explicit constraint for deferred or candidate-only
  capability selection;
- emit complete typed decision and explanation provenance with
  `fallback_used=false`;
- expose `resolve`, `explain`, and document validation through Python and CLI.

The selected route remains candidate metadata. C1 authorizes no activation,
plan, runtime, or effect.

## Rationale

This places stable orchestration mechanics in the SDK while leaving semantic
authority with the capability owner and effect authority with the runtime.
Receipt-bound inputs make the outcome replayable. Explicit ambiguity is safer
than a hidden tie-break, and a fixed integer law makes later quality and cost
experiments attributable to a named resolver version.

## Consequences

- Agents can obtain the same typed route decision from the same exact inputs.
- Every candidate remains inspectable, including rejected and degraded ones.
- A stale, tampered, mixed-owner, or incomplete snapshot fails closed.
- C1 initially resolves only `skill` capabilities.
- Retrieval quality is bounded by the pinned owner projection and must be
  evaluated separately under agent-in-loop trials.
- C2 plan compilation and C3 `AoARunner` remain separate landings.
- No C1 result proves invocation, task benefit, cost reduction, consumer-zero,
  compatibility exit, or predecessor archival readiness.

## Source Surfaces

- `src/aoa_sdk/control_plane/api.py`
- `src/aoa_sdk/control_plane/routing/snapshot.py`
- `src/aoa_sdk/control_plane/routing/resolver.py`
- `src/aoa_sdk/control_plane/routing/data/canonical-routing-source-lock.v1.json`
- `src/aoa_sdk/cli/route.py`
- `mechanics/boundary-bridge/parts/route-resolution-control-plane/`
- `.aoa/workspace.toml`

## Follow-Up Route

Land C2 as a separate runtime-neutral context/plan compiler, then C3-C5
runner, adapter, lifecycle, evidence, and closeout slices. Measure the complete
chain with agent-in-loop trials before making cost or Agent OS benefit claims.

## Verification

Run the part-local C1 suite, source-lock and live runtime smoke checks, public
API/CLI tests, mechanics and SDK source-home validators, the full repository
suite, typing, build, release check, and GitHub CI.
