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

The conditional references retained from this card are: `AGENTS.md`, `DESIGN.md`, `DESIGN.AGENTS.md`, `QUESTBOOK.md`, `quests/README.md`, `README.md`, `ROADMAP.md`, `PARTS.md`.

## Boundaries

- Source quest records live in root `quests/`.
- The human open-obligation index lives in root `QUESTBOOK.md`.
- SDK helper contracts live in their owning mechanics parts.
- Generated quest readers must be derived from source records and must land
  with builder and validator routes.

## Validation

Validation for Questbook paths belongs to the nearest active Questbook part `VALIDATION.md`; broader checks inherit root `VALIDATION.md`.
