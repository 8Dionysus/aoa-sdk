# Routing Consumer Contract

## Owner and stable identity

`aoa-sdk` is the canonical routing producer. The compatibility namespace,
artifact ABI, route layer name, and runtime mirror directory remain
`aoa-routing`; that stable name does not make the predecessor repository a
source dependency.

An active consumer must read one of these SDK-produced forms:

- an admitted canonical routing release archive;
- a materialized runtime mirror whose manifest names `aoa-sdk` as
  `canonical_producer.owner_repo`;
- a deterministic SDK build created from explicit owner inputs for a bounded
  compatibility canary.

An active consumer must not require an `aoa-routing` checkout, import its
producer, or infer current ownership from the stable artifact namespace.

## Preserved boundaries

The stress-recovery input remains
`aoa-stats/generated/stress_recovery_window_summary.min.json`. It is a
descriptive source-owned summary and does not replace
`recommended_paths.min.json`, `owner_layer_shortlist.min.json`, route
explanation, approval, runtime execution, or eval verdicts.

The SDK-owned compatibility witness at
`../examples/composite_stress_route_hint.example.json` preserves the bounded
`composite_stress_route_hint_v1` shape for sibling proof references. It is a
fixture, not a live decision and not a new source of stress, playbook, KAG,
memo, or eval meaning.

## Consumer admission

Before reading a materialized bundle, a consumer must verify:

1. the bundle or mirror manifest identifies `aoa-sdk` as canonical producer;
2. the ABI epoch remains `aoa_routing_thin_router_v1`;
3. required files and their digests match the admitted manifest;
4. provenance and owner-switch receipt remain available;
5. the consumer does not silently fall back to a predecessor checkout.

Historical `aoa-routing` releases, decisions, and repository references remain
valid provenance. Historical identity is not an active checkout requirement.

## Agon gate route

The routing-owned pre-protocol Agon gate surface is supplied by
`aoa_sdk.control_plane.routing.agon` and the wheel-packaged
`data/agon_gate_routing_registry.min.json`. Consumers may read the packaged
registry or rebuild it from the packaged config; they must not look for the
former `aoa-routing/mechanics/agon/parts/gate-routing/` checkout path.

The bridge preserves `agon_gate_routing_registry.v1` and the twelve predecessor
trigger IDs while changing `owner_repo` to `aoa-sdk`. The bridge emits only
advisory route candidates with `runtime_effect=none`.
`Agents-of-Abyss` remains the source owner for Agon law.
