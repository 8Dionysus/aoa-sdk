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

## Accepted Routing Succession Shape

`AOA-SDK-D-0071` accepts a staged succession of the routing producer into the
SDK control plane. Acceptance is not activation. Until the G5 owner-switch
receipt, the live state remains:

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
`AoASDK` behavior or a runtime body. This design section does not authorize
producer code movement or G5.

The disposable R3 migration result lives in
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/evidence/routing-succession-r3-migration-rehearsal.json`.
It proves that a minimal `src/aoa_sdk/control_plane/routing/` producer can
build the fourteen compatibility artifacts from an installed wheel without an
`aoa-routing` checkout and can roll back to the predecessor. The candidate was
removed. G3 authorizes M1 shadow implementation, where inherited typing debt,
schemas, validators, package data, negative fixtures, and dual-producer
provenance must be integrated before release. It does not authorize G5.

## Design as Aim

The long aim is an SDK that lets AoA agents, tools, and humans consume the
federation without turning local path knowledge into hidden authority.

The repository should support:

- explicit workspace discovery and topology resolution;
- typed facades over published sibling surfaces;
- compatibility checks that fail on silent drift;
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

The SDK can inspect, enqueue, and assist bounded local automation. It should not
become a daemon, service runtime, memory store, proof engine, or hidden agent
runner.

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
