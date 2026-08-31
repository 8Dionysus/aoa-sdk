# AGENTS.md

## Applies to

`mechanics/rpg/`.

## Role

Route the shared RPG mechanic for the typed consumer slice and RPG surface-path
helper boundary.

## Relevant routes

The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/rpg/README.md`, `mechanics/rpg/ROADMAP.md`, `mechanics/rpg/parts/README.md`, `mechanics/rpg/parts/typed-consumer-api/README.md`, `mechanics/rpg/parts/surface-path-transport/README.md`, `src/aoa_sdk/rpg/`.

## Boundaries

- Stay on the control plane.
- Do not make SDK helpers gameplay, frontend, or RPG runtime authority.
- Keep surface paths explicit and typed.

## Validation

Validation for RPG paths belongs to the nearest active RPG part `VALIDATION.md`; broader checks inherit root `VALIDATION.md`.

## Closeout

Report whether registry, model, or surface-path helper behavior changed.
