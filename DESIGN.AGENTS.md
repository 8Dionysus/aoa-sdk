# aoa-sdk Agent Surface Design

## Role

`DESIGN.AGENTS.md` describes the desired form of agent-facing guidance within
`aoa-sdk`.

It is not a replacement for root `AGENTS.md`, nested `AGENTS.md` cards, source
code, schemas, generated companions, validators, or decision records.

Use it when the question is agent-facing shape: card placement, reading order,
nearest-card authority, source truth, validation posture, closeout, and return
routes for low-context agents working on the SDK control plane.

Adjacent routes:

- inherited route law: `AGENTS.md`, then the nearest nested `AGENTS.md`
- executable procedure: root `VALIDATION.md` or the nearest part route after
  the touched lane is known
- system form: `DESIGN.md`
- durable rationale: `docs/decisions/`
- owner boundaries: `docs/boundaries.md`
- current direction: `ROADMAP.md`
- validators: `scripts/validate_nested_agents.py`, release checks, and owning
  tests

It answers one question:

What shape should agent-facing surfaces take so SDK work stays bounded,
source-routed, validated, and returnable?

## Design Thesis

`aoa-sdk` should give agents a control-plane guidance mesh:

- a compact root route card;
- local cards near high-risk editable districts;
- source surfaces that keep meaning stronger than instructions;
- validators that make route claims checkable;
- decisions that explain durable topology rationale;
- closeout language that tells the next agent what changed, what was checked,
  what was skipped, and where owner pressure returns.

The root card names the road.
The nearest card narrows the lane.
The source surface owns meaning.
The validator tests the claim.
The closeout returns the work.

## Agent Surface Classes

### Root Card

Root `AGENTS.md` owns repository identity, owner boundaries, start route,
route-away conditions, broad validation posture, GitHub landing workflow, and
closeout expectations.

It should stay readable enough to be the first file an agent reads.

### Design Cards

`DESIGN.md` owns the repository's system form.

`DESIGN.AGENTS.md` owns the desired form of agent-facing guidance. It tells
agents what kind of `AGENTS.md` mesh they are preserving when they add, move,
split, validate, generate, or port local cards.

### Local Cards

Local `AGENTS.md` cards own directory-specific risk, source surfaces, local
stop-lines, and local validation routes.

Current protected local cards include:

- `.aoa/AGENTS.md`
- `.github/AGENTS.md`
- `docs/AGENTS.md`
- `docs/decisions/AGENTS.md`
- `generated/AGENTS.md`
- `skills/AGENTS.md`
- `sdk/AGENTS.md`
- `sdk/public-interface/AGENTS.md`
- `sdk/facade-boundary/AGENTS.md`
- `sdk/runtime-entry/AGENTS.md`
- `sdk/distribution/AGENTS.md`
- `mechanics/AGENTS.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/AGENTS.md`
- `schemas/AGENTS.md`
- `scripts/AGENTS.md`
- `src/aoa_sdk/AGENTS.md`
- `tests/AGENTS.md`

The `mechanics/` package-local cards listed in `mechanics/topology.json` are
also protected route surfaces.

Future durable editable districts should either add a local card or be
explicitly exempted by the validator and root route.

### Source Surfaces

Source code, docs, schemas, examples, decision notes, generated-source inputs,
and validators own meaning within their lane.

Agent guidance should route to them. It should not become source truth by
repeating their claims.

### Generated Companions

Generated files help low-context agents navigate compactly. They remain lower
authority than their builders and authored sources.

When generated output changes, the agent should find the builder, source input,
and check command that produced it.

### Mechanic Cards

The root `mechanics/AGENTS.md` and package-local cards name operation owner,
input, output, source surfaces, stronger owners, provenance bridges,
validation, and closeout.

A mechanic card should not claim importable SDK source ownership. That remains
in `src/aoa_sdk/`. SDK source-home posture now starts at `sdk/AGENTS.md` and
routes to implementation, mechanics, docs, release, or stronger-owner
surfaces.

Functioning mechanic parts add the nearest active work route:
`parts/<part>/README.md` names role, input, output, owner, and next route;
`CONTRACT.md` names may/must-not boundaries; `VALIDATION.md` names executable
proof. Old root paths route through package `PROVENANCE.md` and checked
`former-routes.json` maps; historical receipts remain recoverable in Git.
Active work starts from the current part route.

## Conditional route shape

For ordinary SDK changes, start with root AGENTS.md, then the nearest nested AGENTS.md for every touched path. Open the owner source surface, README, DESIGN, CONTRACT, release, generated, or sibling-owner source only when the touched path, semantic question, or requested operation requires it. Select the narrowest relevant validator through the applicable VALIDATION.md; broaden to release or compatibility gates for structural, generated, route-facing, or release-facing work. Repository-shape, source-home, route-law, or mechanics-topology questions additionally consult DESIGN.md, this design surface, the decision index, and the relevant decision record only when that question is active.

## Design Law

- `AGENTS.md` routes work. It is not the whole design.
- `DESIGN.md` names the system form. It is not executable route law.
- `DESIGN.AGENTS.md` names the agent-facing form. It is not a local card.
- `docs/decisions/` preserves rationale. It is not active source truth.
- `sdk/` owns SDK source-home posture and route shape.
- `skills/` owns callable procedures over SDK-owned helper contracts, not
  runtime, operator, memory, proof, or playbook meaning.
- `src/aoa_sdk/` owns importable typed SDK implementation.
- `docs/` explains SDK posture and boundaries.
- `schemas/` owns helper contract shape.
- `examples/` owns public-safe examples and fixtures.
- `generated/` remains derived.
- `scripts/` owns deterministic builders and validators.
- `tests/` owns regression proof for expected behavior.
- `mechanics/` owns repeatable operation topology, not SDK source code. It also
  owns part-local homes for single-mechanic artifacts, and its topology map
  owns source-family routing.
- Tool-native template names such as Git hook filenames or user unit filenames
  stay inside the owning part-local route; they do not define root guidance
  districts.

## Canonical Card Shape

Durable local `AGENTS.md` cards should usually begin from this shape:

```markdown
# AGENTS.md

## Applies to

## Role

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory.

## Boundaries

## Validation handoff

Validation posture is inherited from root `AGENTS.md`; executable procedure is
selected through root or path-relative `VALIDATION.md`. A child card names only
the applicable route or local stop-line and does not repeat repository-wide
gate details.

## Closeout
```

Optional sections may be added when they sharpen the local route: `Purpose`,
`Owner lane`, `Source surfaces`, `Generated surfaces`, `Decision review`,
`Legacy posture`, `Runtime boundary`, `Post-change route review`, or package
equivalents.

## Stop-Lines

Agent guidance must not:

- turn SDK facades into sibling-source authority;
- hide path guessing behind convenience;
- treat generated companions as source truth;
- treat checkpoint or closeout artifacts as reviewed memory, proof, or
  progression verdicts;
- convert `aoa skills ...` into a non-skill activation route;
- make the SDK a runtime service, daemon, or hidden agent runner;
- use `sdk/` as a second implementation tree or as cosmetic symmetry;
- widen `mechanics/` by cosmetic analogy;
- bury semantic changes under "docs-only" wording.

## Decision Review

When agent-facing topology changes in a way future contributors will need to
understand, add or update a decision record under `docs/decisions/`.

Decision records explain why a route, placement, validator, owner split, or
source-home rule exists. They do not replace active route cards or source
surfaces.

## Validation Direction

Executable procedures live in root `VALIDATION.md` and the nearest applicable
part `VALIDATION.md`. This design surface names what validation should prove:

- required local route cards exist and preserve owner boundaries;
- SDK source-home branches have local route cards and manifest coverage;
- generated companions are reproducible;
- decision indexes are current;
- source-home and mechanics topology changes have rationale;
- compatibility checks do not hide missing sibling surfaces;
- release-facing changes run broad gates after narrow checks.

## One-Line Rule

Agent guidance in `aoa-sdk` should help an agent find the source owner, keep
the SDK on the control plane, validate the crossing, and hand stronger meaning
back to its owner.
