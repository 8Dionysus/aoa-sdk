# Agon Gate Routing Bridge Contract

## Function

Build and validate one deterministic SDK-owned registry of advisory Agon gate
route hints while preserving center and sibling-owner authority.

## Compatibility

- `schema_version` remains `agon_gate_routing_registry.v1`;
- the twelve predecessor trigger IDs and route-action mapping remain stable;
- `owner_repo` moves from `aoa-routing` to `aoa-sdk`;
- active self-return next hops move from `aoa-routing` to `aoa-sdk`;
- the final validation invariant names `aoa-sdk` as the control-plane owner;
- the owner-dispatch seam becomes `aoa-sdk.owner-dispatch-seam.v1`.

The Agon registry was not one of the fourteen root G5 routing ABI artifacts.
This bridge implements the R0 `merge` disposition without modifying the
immutable G5 corpus or pretending that the predecessor checkout is still a
source dependency.

## May

- emit pre-protocol route candidates;
- request missing context or owner review;
- recommend a quarantine handoff;
- load optional center lawful-move vocabulary for drift validation;
- package the registry and schemas in the SDK wheel.

## Must Not

- open an arena or create a live session;
- activate capabilities or dispatch runtime effects;
- grant closure, summon, contestant, judge, or verdict authority;
- write scars, schedule retention, mutate rank, or promote ToS state;
- copy center, agent, eval, memo, playbook, stats, KAG, or ToS meaning;
- require an `aoa-routing` checkout.

## Validation

Executable checks live in [VALIDATION](VALIDATION.md).
