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
| `src/aoa_sdk/` | importable typed SDK source home and CLI behavior |
| `docs/` | authored explanation for boundaries, workspace layout, compatibility, release, checkpoint, closeout, and control-plane posture |
| `docs/decisions/` | durable rationale for topology, route-law, source-home, validation, and mechanics choices |
| `mechanics/` | repeatable SDK operation topology; skeleton cards, source maps, and package route law |
| `.aoa/` | workspace metadata and local control-plane runtime artifacts, not hidden source truth |
| `schemas/` | SDK helper contract schemas |
| `examples/` | public-safe contract examples and fixtures |
| `generated/` | derived control-plane companions and compact read models |
| `scripts/` | deterministic builders, validators, release helpers, and operator utilities |
| `tests/` | regression and contract checks |
| `githooks/` | optional local git-boundary integration that stays active-session-only |
| `systemd/` | optional user-service units for bounded local automation |
Each class may support the others. No class should silently steal another
class's authority.

## SDK Source Home Rule

The importable SDK source home is `src/aoa_sdk/`.

A top-level `sdk/` district should not be introduced merely because this
repository is named `aoa-sdk` or because sibling repositories have domain
source homes such as `agents/`, `memo/`, `evals/`, `skills/`, or `techniques/`.

If a future top-level `sdk/` directory appears, it needs a distinct owner role,
route card, validation path, and decision record. It must not duplicate or
rename `src/aoa_sdk/` by cosmetic analogy.

## Mechanics Posture

`mechanics/` packages name repeatable SDK operations that cross several
surfaces: source, docs, schemas, examples, generated companions, scripts,
tests, compatibility checks, or handoff artifacts.

Mechanics do not replace the Python source lane. They route operation pressure
around it.

Shared AoA mechanics should keep shared names when the operation is truly the
same recurring shape. Local SDK mechanics are allowed only when the operation
has its own trigger, input, output, owner split, stop-line, validation, and
reason that cannot be represented as a part of a shared mechanic.

## Design as Operation

A healthy SDK operation follows a bounded route:

1. Identify the source-owned sibling surface or SDK-owned helper surface.
2. Load it through explicit workspace configuration or a documented override.
3. Preserve truth labels such as source, generated, candidate, manual,
   reviewed, activated, or advisory.
4. Expose typed access without absorbing owner meaning.
5. Validate schema, generated parity, compatibility, and relevant behavior.
6. Hand off stronger claims to the owning repository.

Control-plane power is useful only while it remains inspectable and reversible.

## Design as Aim

The long aim is an SDK that lets AoA agents, tools, and humans consume the
federation without turning local path knowledge into hidden authority.

The repository should support:

- explicit workspace discovery and topology resolution;
- typed facades over published sibling surfaces;
- compatibility checks that fail on silent drift;
- generated capsules for low-context orientation;
- bounded CLI helpers for inspection, activation, checkpoint, closeout,
  release, and handoff routes;
- portable behavior across local checkouts, export bundles, and future
  transport layers;
- mechanics packages that make recurring SDK operations easier to review
  without widening SDK ownership.

## Design Principles

### 1. Control plane before authority

The SDK may load, validate, expose, activate, suggest, and hand off. It should
not become the source of truth for skills, evals, memo, agents, routing,
playbooks, KAG, stats, runtime, or progression meaning.

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
sibling change behind permissive fallback behavior, it weakens the SDK.

### 7. Mechanics after rationale and design, before payload movement

Mechanics packages land after the decision and design surfaces can name why the
package exists, what it owns, which stronger owners remain outside, and how the
move is validated. Payload moves need a separate package-local reason and
validator.

### 8. Python source stays boring

`src/aoa_sdk/` should remain a normal Python source home. Domain-specific
operation topology belongs in docs, generated companions, scripts, tests, or
mechanics when those surfaces have a real owner role.

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
- hidden path guessing or silent sibling fallback;
- generated files cited as authority;
- checkpoint or closeout artifacts treated as reviewed memory, proof, or
  progression verdicts;
- runtime language pretending the SDK is a service body;
- a top-level `sdk/` directory introduced as cosmetic symmetry;
- mechanics packages that only rename folders without an operation owner;
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
