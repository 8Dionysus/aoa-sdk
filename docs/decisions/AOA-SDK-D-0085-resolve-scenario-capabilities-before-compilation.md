# Resolve Scenario Capabilities Before Compilation

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0085
- Original date: 2026-07-26
- Surface classes: public API, model contract, plan compiler, owner projection
- SDK facets: control-plane, public interface, facade boundary
- Mechanic parents: boundary-bridge
- Guard families: owner provenance, scenario identity, migration binding, fail closed
- Posture: accepted

## Context

C1 resolves an agent intent to one advertised entry route. C2 compiles an
admitted `aoa-playbooks` scenario contour whose abstract capability
requirements may differ from that entry route. The original C2 fixtures made
the first contour capability and agent double as the selected route candidate.
That shortcut hid three facts exposed by the live G8 chain:

- the selected skill explains entry into a scenario but is not necessarily a
  step in the scenario DAG;
- `RouteIntent.requested_by` is the caller, not the provider of every
  capability in the scenario;
- current `aoa-skills` migration records resolve legacy playbook requirements
  to capability-graph nodes with different semantic owners and availability
  postures, including an explicitly unbound runtime guard.

Requiring the selected route capability and caller to occur in the contour
would either reject valid owner composition or synthesize false ownership.

## Decision

Introduce `aoa_control_plane_plan_compiler_v2` and an owner-qualified scenario
binder before compilation.

- The selected `RouteCandidate.scenario` must exactly equal the admitted
  `ScenarioRef`; an implicit or absent scenario fails closed.
- The route decision remains the immutable explanation of the entry
  capability and candidate metadata.
- Each authored `aoa-playbooks` capability requirement is separately bound,
  in contour order, through the exact pinned `aoa-skills` migration record and
  capability graph node.
- `ScenarioCapabilityBinding` preserves the authored requirement alias,
  resolved capability identity, semantic owner, migration action and
  compatibility, availability, lifecycle posture, and migration provenance.
- Required agents, eval contracts, and retention contracts are resolved from
  exact Git objects pinned by the same routing snapshot.
- The compiler maps playbook step aliases through those bindings. It does not
  require the route entry capability, caller, or candidate agent to appear in
  the scenario DAG.
- Legacy exact `ScenarioBinding` inputs remain accepted during the
  compatibility window, but new public construction uses the binder.

## Rationale

The split preserves the authority chain instead of flattening it:
`aoa-playbooks` owns authored composition, `aoa-skills` owns the migration and
capability graph, semantic owners retain their declared meaning, and
`aoa-sdk` owns only deterministic resolution and compilation. An `unbound` or
`unavailable` owner node stays visible as such; binding records it but does not
activate, authorize, or promote it.

## Consequences

- Positive: live C1 decisions can compile all three admitted golden scenarios
  without fabricated agent, capability, eval, or memo references.
- Positive: entry-route and scenario-step identities are independently
  inspectable and content-addressed.
- Positive: owner or snapshot drift fails before plan construction.
- Tradeoff: callers must name the intended scenario in `RouteIntent` before
  binding and supply reviewed inputs and conditions separately.
- Tradeoff: legacy bindings remain a compatibility surface until the migration
  window closes.
- Stop line: a resolved binding or compiled plan is not capability
  availability, activation, runtime authorization, execution, or proof of
  benefit.

## Source Surfaces

- `src/aoa_sdk/contracts/control_plane.py`
- `src/aoa_sdk/control_plane/planning/bindings.py`
- `src/aoa_sdk/control_plane/planning/compiler.py`
- `mechanics/boundary-bridge/parts/plan-compilation-control-plane/`

## Follow-Up Route

Exercise the public installed-wheel C1-to-C2 chain against exact owner pins,
then carry only the immutable `RunPlan` into the C3 runner and runtime-owner
adapter route.

## Verification

Run the plan-compilation focused tests, deterministic example check,
installed-wheel probe, and the three-scenario public golden-chain verifier
listed in the part validation card.

## Current Applicability

As of 2026-07-28:

- Still valid: route-entry identity remains separate from scenario
  participants, and every scenario requirement remains owner-bound before
  compilation.
- Changed: current `aoa-playbooks` contours carry exact
  `aoa-skills/generated/capability_graph.json` node IDs rather than legacy
  skill aliases.
- Compatibility: the binder resolves an exact graph ID directly and reads
  `capabilities/legacy-skill-migration.yaml` only when a legacy contour alias
  is not itself a graph node.
- ABI preservation: `ScenarioCapabilityBinding.migration_provenance` remains
  the public compatibility field. For a direct ID it cites the exact graph
  node; for a legacy alias it cites the migration entry.
- Superseded by: none.

## Review Log

### 2026-07-28 - Prefer exact graph identity over migration lookup

- Classified the mismatch as semantic supersession of the original
  alias-first owner input, not a change to route-entry separation or plan
  meaning.
- Removed the unnecessary migration-ledger read from the current exact-ID
  path.
- Retained alias resolution as a tested compatibility path without inventing
  an ABI for navigation-only nodes or moving capability meaning into the SDK.
