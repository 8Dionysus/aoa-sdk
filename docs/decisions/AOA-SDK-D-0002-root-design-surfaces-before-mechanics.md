# Root Design Surfaces Before Mechanics

## Status

Accepted.

Partially superseded by `AOA-SDK-D-0043` for the top-level `sdk/` source-home
rule.

## Index Metadata

- Decision ID: AOA-SDK-D-0002
- Original date: 2026-05-31
- Surface classes: root/topology, design route, agent guidance
- SDK facets: design surface, agent surface, mechanics prep, source home
- Mechanic parents: none
- Guard families: source topology, route law, agent mesh
- Posture: accepted

## Context

After adding the decision rationale lane, `aoa-sdk` still lacked the root
design surfaces that already exist in the refactored AoA repositories.

Without `DESIGN.md`, the next `mechanics/` move would have to infer the SDK's
system form from `README.md`, `AGENTS.md`, `ROADMAP.md`, and scattered docs.
Without `DESIGN.AGENTS.md`, route-card changes would have no local design
surface explaining how root and nested guidance should cooperate.

The missing layer also left an important SDK-specific question too implicit:
at that point the importable implementation lane was already `src/aoa_sdk/`.
A cosmetic sibling-analogy directory should not appear unless it has a
distinct owner role and decision.

`AOA-SDK-D-0043` later supplies that distinct owner role, route-card mesh,
manifest, and validator. The original warning remains valid only against
cosmetic `sdk/` symmetry.

## Options Considered

- Introduce `mechanics/` first and let package-local cards define the shape.
- Keep design meaning inside `README.md`, `AGENTS.md`, or `ROADMAP.md`.
- Copy a sibling `DESIGN.md` and `DESIGN.AGENTS.md` without local SDK
  boundaries.
- Add local root design surfaces first, then use decisions and validators to
  guide mechanics work.

## Decision

Create root `DESIGN.md` and `DESIGN.AGENTS.md` before introducing
`mechanics/`.

`DESIGN.md` owns the system form of the SDK control plane.
`DESIGN.AGENTS.md` owns the desired form of agent-facing guidance within the
repository.

`src/aoa_sdk/` remains the importable SDK implementation lane.

This decision originally required a future top-level `sdk/` district to have a
distinct role, local route card, validation path, and decision record.
`AOA-SDK-D-0043` satisfies that condition and establishes `sdk/` as the
checked SDK source-home tree.

## Rationale

The SDK sits between sibling source truth, typed Python access, generated
companions, compatibility checks, checkpoint and closeout helpers, and future
mechanics. That makes the system form itself a protected route surface.

The design layer prevents `mechanics/` from becoming a cosmetic folder
migration. It also keeps root `AGENTS.md` from swelling into every design
argument and keeps `README.md` focused on entry routing.

The local SDK source-home rule belongs in design before mechanics because
mechanics should route repeatable operations around the SDK source lane, not
rename or absorb it.

## Consequences

- Future topology work has a stable system-design route before touching
  mechanics.
- Agent-facing card changes can be reviewed against `DESIGN.AGENTS.md`.
- `src/aoa_sdk/` is explicitly protected from cosmetic top-level `sdk/`
  pressure. After `AOA-SDK-D-0043`, the active split is `sdk/` for SDK
  source-home posture and `src/aoa_sdk/` for importable Python implementation.
- Mechanics work should now update or cite decisions and design surfaces when
  it changes owner split, package names, validation authority, or source-home
  posture.
- The design files remain weaker than active source code, validators,
  generated-source inputs, and sibling-owner truth.

## Source Surfaces

- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `AGENTS.md`
- `README.md`
- `ROADMAP.md`
- `docs/boundaries.md`
- `docs/decisions/README.md`
- `src/aoa_sdk/AGENTS.md`
- `scripts/validate_nested_agents.py`

## Follow-Up Route

Use `DESIGN.md`, `DESIGN.AGENTS.md`, this decision, and `AOA-SDK-D-0043`
before changing `sdk/`, `mechanics/`, or any top-level SDK support district.
Mechanics decisions should name whether each package is a shared AoA mechanic,
a mechanic part, or a justified local SDK mechanic.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
