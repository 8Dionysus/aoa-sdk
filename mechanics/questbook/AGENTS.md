# AGENTS.md

## Applies to

This card applies to `mechanics/questbook/` and all descendants.

## Role

Questbook is the SDK operation package for source quest record placement,
public obligation indexing, lifecycle posture, and dispatch-reader posture.

Stay on the control plane. This mechanic makes obligations visible and
returnable; it does not turn a quest into a proof verdict, owner acceptance,
runtime action, release readiness, or Agon authority.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `AGENTS.md`, `DESIGN.md`, `DESIGN.AGENTS.md`, `QUESTBOOK.md`, `quests/README.md`, `README.md`, `ROADMAP.md`, `PARTS.md`.

## Boundaries

- Source quest records live in root `quests/`.
- The human open-obligation index lives in root `QUESTBOOK.md`.
- SDK helper contracts live in their owning mechanics parts.
- Generated quest readers must be derived from source records and must land
  with builder and validator routes.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.
