# aoa-sdk System Design

## Role

`DESIGN.md` describes the system form of `aoa-sdk`.

It is not the public entrypoint, charter, roadmap, release note, decision
record, generated capsule, or agent instruction file.

Use it when the question is repository shape, owner boundaries, source-home
placement, generated companions, compatibility posture, or how `mechanics/`
packages should relate to the SDK source lane.

Adjacent routes:

- public entry: `README.md`
- agent route card: `AGENTS.md`
- agent-facing guidance form: `DESIGN.AGENTS.md`
- current direction: `ROADMAP.md`
- owner boundaries: `docs/boundaries.md`
- durable rationale: `docs/decisions/`
- mechanics operation topology: `mechanics/`
- SDK source home: `sdk/`
- SDK-local statistical port: `stats/`
- SDK-owned skill home: `skills/`
- importable SDK source: `src/aoa_sdk/`
- generated control-plane capsule: `generated/workspace_control_plane.min.json`

It answers one question:

What shape should the typed AoA control-plane SDK preserve while it grows?

## Design Thesis

`aoa-sdk` is the typed local-first control-plane helper for the AoA
federation.

It consumes source-owned sibling surfaces, exposes stable Python and CLI access
to them, validates compatibility, labels truth posture, and hands work back to
the owning repository when meaning changes.

The SDK owns the handle.
The sibling owns the meaning.
The generated companion helps orientation.
The validator keeps the crossing honest.

## Design as Appearance

The repository should appear as a compact control-plane console:

- a clear public entry route;
- a visible source-owner boundary;
- a tree-shaped SDK source home for public-interface, facade-boundary,
  runtime-entry, and distribution posture;
- a Python package with typed facades and loaders;
- authored docs for workspace, compatibility, release, and handoff posture;
- decision records for durable topology rationale;
- schemas and examples for SDK helper contracts;
- deterministic builders and validators;
- generated companions that point back to sources;
- local route cards near high-risk surfaces.

A reader should be able to ask: what does the SDK own, which sibling owns the
meaning, which surface is source versus derived, which command proves parity,
and where does the next stronger claim return?

## Design as Anatomy

`aoa-sdk` is composed of different authority classes.

| District | Role |
| --- | --- |
| root surfaces | public entry, route law, design form, roadmap direction, release posture |
| `sdk/` | source-authored SDK home for public-interface, facade-boundary, runtime-entry, and distribution posture |
| `src/aoa_sdk/` | importable typed SDK implementation and CLI behavior |
| `docs/` | authored root explanation for boundaries, workspace layout, compatibility, release route doors, decisions, and control-plane posture |
| `docs/decisions/` | durable rationale for topology, route-law, source-home, validation, and mechanics choices |
| `evals/` | SDK-local eval pressure port for intake, suites, and reports before proof adoption by `aoa-evals` |
| `stats/` | SDK-local measurement questions and evidence-linked reference packets; shared statistical grammar remains in `aoa-stats` |
| `skills/` | canonical callable procedures over SDK-owned Titan helper contracts; admission is local, while global exposure is a derived OS-profile concern |
| `mechanics/` | repeatable SDK operation topology, part-local artifact homes, source maps, and package route law |
| `.aoa/` | workspace metadata and local control-plane runtime artifacts, not hidden source truth |
| `schemas/` | shared SDK helper contract schemas and root-published generated contracts |
| `examples/` | public-safe shared examples and cross-mechanic fixtures when present |
| `generated/` | derived control-plane companions and compact read models |
| `quests/` | lane/state source quest records and durable SDK obligations |
| `scripts/` | deterministic repo-wide builders, validators, release helpers, and shared operator utilities |
| `tests/` | repo-wide regression, route, and contract checks |
| `mechanics/<parent>/parts/<part>/` | single-mechanic config, docs, schemas, examples, generated companions, manifests, helper contracts, scripts, tests, and local automation templates |
Each class may support the others. No class should silently steal another
class's authority.

## Owner Skill Home Rule

The SDK skill home is `skills/`. It contains only procedures whose helper
behavior is owned by this repository. The packages may compose SDK witnesses
and candidates, but they cannot turn those artifacts into runtime execution,
operator authentication, durable memory, proof, or playbook authority.

The owner package is source truth. Semantic trees, typed relation graphs, KAG
records, and the managed user installation are derived views. Repository-local
duplicates are forbidden for bundles exposed through the OS user profile, and
task-local execution DAGs remain with the executing session.

## SDK Source Home Rule

The SDK source home is `sdk/`.

It is a tree-shaped route home for SDK-owned posture: public interface,
facade boundary, runtime entry, and distribution promises. Its checked contract
is `sdk/source_home.manifest.json`, and its nearest route law starts at
`sdk/AGENTS.md`.

The importable SDK implementation remains `src/aoa_sdk/`.

`sdk/` must not duplicate, rename, or absorb `src/aoa_sdk/`. It must not use
mechanic `PARTS.md` vocabulary. Its branches route to implementation,
mechanic, docs, release, or stronger-owner surfaces; they do not replace
those surfaces.

## Mechanics Posture

`mechanics/` packages name repeatable SDK operations that cross several
surfaces: source, docs, schemas, examples, generated companions, scripts,
tests, compatibility checks, or handoff artifacts.

Mechanics do not replace the Python source lane. They route operation pressure
around it.

Single-mechanic payload belongs below the owning part. If a file is a Git hook
template, user unit template, schema, fixture, generated companion, operator
script, or regression for one operation, the active route should be
`mechanics/<parent>/parts/<part>/<district>/...`. External tool-native
filenames may remain native inside that route, but they must not become root
district names by inertia.

Every `src/aoa_sdk/*` family must have a route in
`mechanics/topology.json#source_family_routes`. A source family name alone is
not evidence for a parent mechanic; it may be a facade, loader, command entry,
or part of a shared parent operation.

Top-level mechanics follow the shared AoA parent vocabulary when that
vocabulary already carries the operation. Local SDK lanes such as
compatibility, skill inspection, surface detection, workspace topology, closeout,
A2A return, or Codex deploy status should live as parts unless they can prove
an independent parent operation, owner split, stop-line, and validator that
cannot be represented inside a shared parent.

## Design as Operation

A healthy SDK operation follows a bounded route:

1. Identify the source-owned sibling surface or SDK-owned helper surface.
2. Load it through explicit workspace configuration or a documented override.
3. Preserve truth labels such as source, generated, candidate, manual,
   reviewed, owner-accepted, executed, or advisory.
4. Expose typed access without absorbing owner meaning.
5. Validate schema, generated parity, compatibility, and relevant behavior.
6. Hand off stronger claims to the owning repository.

Control-plane power is useful only while it remains inspectable and reversible.

## Organ Access Control Plane

The organ access plane is a protocol-independent SDK control-plane surface.
MCP is one adapter, not its owner model.

```text
owner records + private desired state + stack observations + proof refs
  -> validated registry projection
  -> catalog
  -> inspect organ
  -> inspect capability
  -> compile activation plan
  -> host-authorized direct owner connection
  -> receipt
```

The configured workspace owns one explicit private registry source instance.
`aoa-sdk` owns its schema, typed models, deterministic projection, discovery,
compatibility comparison, and activation-plan compiler. `abyss-stack` supplies
runtime observations and executes approved lifecycle work. Owner repositories
retain payload meaning, and `aoa-evals` retains proof interpretation.

Discovery never activates a server. A plan is content-addressed candidate
intent with exact owners, capabilities, effects, credentials classes,
preconditions, evidence references, expiry, and rollback route. Execution
belongs to the host or runtime owner and must return a receipt before the
registry may observe a stronger maturity state.

The registry is deny-by-default. It can suppress discovery, compare desired
and observed schemas, and route a consumer to a direct owner endpoint. It
cannot infer domain truth, proof, freshness, or acceptance from its own fields,
and it is not a proxy for owner tools.

## Cross-Organ Orchestration

When one OS task crosses several direct owner access planes, `aoa-sdk` may
validate the chain but may not execute it:

```text
host intent
  -> KAG evidence
  -> memo candidate
  -> eval request
  -> eval result
  -> explicit owner acceptance or rejection
```

The request pins every owner schema digest and source revision. Each stage
binds the previous content-addressed run snapshot, exact input and output,
freshness, effect state, owner evidence, host receipt, and next owner. The SDK
accepts only one stage per call and reconstructs the entire chain during
validation.

The host, normally `abyss-stack`, selects transport, holds credentials, calls
the direct owner, issues the host receipt, and performs lifecycle or rollback.
KAG, memo, and eval owners retain their meaning. The state machine is not a
workspace MCP tool and cannot infer owner acceptance from proof or model
confidence.

## Accepted Routing Succession Shape

`AOA-SDK-D-0071` accepts a staged succession of the routing producer into the
SDK control plane. The completed pre-G5 state was:

```text
predecessor_canonical:
  canonical producer: aoa-routing
  SDK posture: typed consumer and accepted successor
```

The migration then permits one temporary `sdk_shadow` state in which the SDK
can build non-publishing parity output while `aoa-routing` remains canonical.
Only after parity, rollback, consumer, runtime-mirror, and trust evidence pass
may the receipt establish:

```text
sdk_canonical:
  canonical producer: aoa-sdk
  predecessor posture: compatibility and rollback only
```

The function moves, not the predecessor repository form. Public routing paths
and `aoa_routing_thin_router_v1` remain stable during the owner-only switch.
Source organs retain authored meaning. `AoARunner` remains a lifecycle client
of external runtime adapters; activation and model/tool execution remain with
the runtime owner.

The checked authority matrix, compatibility exit conditions, repository
succession states, and archive stop-line live in
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/evidence/routing-succession-r1-target-operating-model.json`.
The runtime-neutral R2 types, lifecycle graph, replay rules, three golden
scenarios, and threat controls live in
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/docs/routing-succession-r2-agent-os-contracts.md`
and `src/aoa_sdk/contracts/control_plane.py`. They define protocols, not active
`AoASDK` behavior or a runtime body by themselves. C1-C4 now implement bounded
control-plane behavior and one explicit runtime transport client over those
contracts, while runtime execution remains external. The R2 contracts alone
did not authorize producer movement; the
G3-authorized M1 slice below was shadow-only and did not authorize G5.

The disposable R3 migration result lives in
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/evidence/routing-succession-r3-migration-rehearsal.json`.
It proves that a minimal `src/aoa_sdk/control_plane/routing/` producer can
build the fourteen compatibility artifacts from an installed wheel without an
`aoa-routing` checkout and can roll back to the predecessor. The candidate was
removed. The resulting M1 implementation now lives under
`src/aoa_sdk/control_plane/routing/`: it resolves the inherited typing debt,
packages schemas and a strict validator, preserves the fourteen predecessor
bytes, emits dual-producer provenance, rejects canonical-looking publication
targets, and is checked from an installed wheel. `aoa-routing` still remains
canonical. The passed G4 chain and predecessor conditional handoff now permit
one explicit next posture: the installed SDK can build a non-publishing
`sdk_g5_candidate` assembly carrying SDK producer identity, exact clean input
refs, complete artifact subjects, and no switch authority. That candidate is
input to stronger-owner artifact trust and runtime canary review, not the G5
receipt. After that canary and rollback evidence passed,
`AOA-SDK-D-0072` added a separately profiled public release envelope around
the exact candidate. It binds release bytes, source refs, and the
stronger-owner verifier while normal runtime and every switch-authority flag
remain denied. `AOA-SDK-D-0076` now closes the owner-only transition with a
receipt-bound canonical envelope. It reconstructs the exact `v0.7.0` routing
assembly, requires byte parity with the immutable public asset, binds the
exact `abyss-stack` cutover contract, and makes `aoa-sdk` the single canonical
producer. The release itself authorized but did not execute live runtime
mutation. Stronger-owner admission and the separate `abyss-stack` cutover have
since executed from that exact receipt; the predecessor remains retained for
compatibility and rollback. Compatibility exit, consumer-zero, and archival
authority remain separate later gates.

## C1 Route Resolution Shape

`AOA-SDK-D-0077` implements the first callable Agent OS control-plane slice.
`AoASDK.control_plane.resolve()` intersects the trusted SDK-canonical routing
registry with the exact pinned `aoa-skills` capability graph.
`AoASDK.control_plane.explain()` accounts for the resulting decision without
rerouting.

```text
RouteIntent
  + SDK-canonical G5 runtime manifest and source lock
  + pinned aoa-skills capability projection
  -> RouteDecision
  -> RouteExplanation
```

The snapshot fails closed on trust, receipt, digest, path, ref, or owner
binding drift. Resolution uses only owner projection retrieval fields and a
published integer score law. Equal eligible top scores block; lexical order is
serialization only and never a semantic fallback. C1 resolves `skill`
candidates only. Deferred and candidate-only capabilities require an exact
explicit constraint.

A selected route is not activation. C1 does not compile a `RunPlan`, select a
runtime adapter, invoke a skill, or execute an effect. C2 compilation and C3
lifecycle coordination are separately bounded surfaces.

## C2 Plan Compilation, C3 Lifecycle, and C4 Transport Shape

`AOA-SDK-D-0078` keeps C2 compilation deterministic and runtime-neutral.
`AOA-SDK-D-0081` makes `AoARunner` a lifecycle client over one explicit
caller-supplied adapter:

```text
RouteDecision + ScenarioBinding + RuntimeProfile
  -> immutable RunPlan
  -> SessionHandle
  -> exact runtime observation
  -> command receipt + append-only events + RunStatus
  -> runtime-owned RunOutcome
  -> owner-complete CloseoutBundleRef
```

The Runner owns admission and reconciliation, not execution. It never discovers
an adapter, invokes a plan step, or creates eval, memo, checkpoint, or evidence
truth. The SDK-owned reference adapter is a deterministic lifecycle witness
with `executes_plan_steps=false`. `AOA-SDK-D-0082` adds the C4
`AbyssStackRuntimeAdapter` as a transport-only production client:

```text
absolute owner profile + exact constraint locations
  -> hashed RuntimeProfile
  + exact RunPlan source/ABI delivery binding
  + explicit no-shell subprocess transport
  -> abyss-stack-owned durable runtime bridge
```

The client can cause execution only through that external bridge. It neither
executes a plan step nor discovers a runtime, policy, executable, or adapter.
Installed-client proof is package proof, not runtime invocation proof.

## Design as Aim

The long aim is an SDK that lets AoA agents, tools, and humans consume the
federation without turning local path knowledge into hidden authority.

The repository should support:

- explicit workspace discovery and topology resolution;
- typed facades over published sibling surfaces;
- compatibility checks that fail on silent drift;
- deterministic, explainable route decisions from exact owner projections;
- generated capsules for low-context orientation;
- bounded CLI helpers for inspection, checkpoint evidence materialization,
  release, and handoff routes;
- portable behavior across local checkouts, export bundles, and future
  transport layers;
- mechanics packages that make recurring SDK operations easier to review
  without widening SDK ownership.

## Design Principles

### 1. Control plane before authority

The SDK may load, validate, inspect, expose, and hand off. It should
not become the source of truth for skills, evals, memo, agents, playbooks,
KAG, stats, runtime, or progression meaning. Accepted routing succession
transfers only routing producer and navigation ABI authority after G5; it does
not transfer sibling-domain meaning.

### 2. Source owner before facade

Typed APIs should point back to the source-owned surface whose meaning they
consume. A convenient facade is not a transfer of ownership.

### 3. Explicit workspace before magical discovery

Workspace root, sibling lookup, mirrors, overrides, and portability seams should
be visible in configuration, docs, and tests.

### 4. Typed contracts before markdown scraping

Prefer stable generated contracts, schemas, manifests, and typed models over
ad hoc extraction from authored prose.

### 5. Generated companions are lower authority

Generated files compress and route. They must remain reproducible and point
back to stronger authored or source-owned surfaces.

### 6. Compatibility before convenience

A new helper is healthy when it makes drift more visible. If it only hides
sibling change behind permissive alternate path behavior, it weakens the SDK.

### 7. Mechanics after rationale and design, with explicit payload movement

Mechanics packages land after the decision and design surfaces can name why the
package exists, what it owns, which stronger owners remain outside, and how the
move is validated. Payload moves need a package-local part, active contract,
package provenance route, topology-map update, and validator.

Single-mechanic artifacts should move from root technical districts into
`mechanics/<parent>/parts/<part>/<district>/...` once the part owns their
role. Root paths remain only for public, repo-wide, shared, or tooling-facing
contracts.

### 8. Python source stays boring

`src/aoa_sdk/` should remain a normal Python implementation home.
SDK source-home posture belongs in `sdk/`. Domain-specific operation topology
belongs in docs, generated companions, scripts, tests, or mechanics when those
surfaces have a real owner role.

### 9. Runtime remains outside

The SDK can inspect, enqueue, coordinate a typed lifecycle through an explicit
adapter, and assist bounded local automation. It should not become a daemon,
service runtime, memory store, proof engine, or hidden execution engine.

### 10. Handoff before absorption

When the SDK discovers a durable pressure that belongs to a sibling owner, it
should make the handoff inspectable instead of becoming a second owner.

## Good Design Feels Like

A consumer can find the typed API.
An agent can find the nearest route card.
A generated capsule can find its builder.
A compatibility failure can find the missing sibling surface.
A checkpoint note can find its review boundary.
A handoff can find the owner repository.
A mechanic can find its decision and validator.
A topological question can find why the route exists.

## Bad Design Smells Like

- SDK helpers presented as source truth;
- hidden path guessing or silent sibling alternate-path acceptance;
- generated files cited as authority;
- checkpoint or closeout artifacts treated as reviewed memory, proof, or
  progression verdicts;
- runtime language pretending the SDK is a service body;
- `sdk/` used as a second implementation tree or as cosmetic symmetry;
- `sdk/` branches without `AGENTS.md`, manifest coverage, and validation;
- mechanics packages or parts that only rename folders without an operation
  owner and validation route;
- compatibility checks that pass by ignoring missing owner surfaces;
- broad "agentic" behavior without truth labels, review, or return routes.

## Relationship to Other Root Surfaces

[`README.md`](README.md) introduces the repository.
[`AGENTS.md`](AGENTS.md) routes agent work.
[`DESIGN.AGENTS.md`](DESIGN.AGENTS.md) holds the design form of the
agent-facing guidance layer.
[`ROADMAP.md`](ROADMAP.md) names current direction.
[`docs/boundaries.md`](docs/boundaries.md) separates owner truth.
[`docs/decisions/`](docs/decisions/README.md) preserves durable rationale.
[`docs/workspace-layout.md`](docs/workspace-layout.md) explains workspace
discovery.
[`docs/versioning.md`](docs/versioning.md) explains compatibility posture.
[`sdk/`](sdk/README.md) is the source-authored SDK home.

`DESIGN.md` holds the system form of the SDK control plane.

## Use by Agents

Agents should consult this file when a change alters:

- repository shape;
- root surfaces;
- source-home placement;
- workspace discovery posture;
- source versus generated authority;
- typed facade boundaries;
- compatibility semantics;
- checkpoint, closeout, release, or handoff posture;
- `mechanics/` package placement;
- agent-facing layer design.

This file does not override local owner truth. It tells agents what kind of
SDK shape they are preserving.
