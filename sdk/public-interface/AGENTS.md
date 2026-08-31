# AGENTS.md

## Applies To

This card applies to `sdk/public-interface/`.

## Role

`sdk/public-interface/` names the public SDK contract posture for Python API,
CLI, and typed model surfaces.

It routes consumer-facing promises to implementation and tests without making
this source-home branch stronger than `src/aoa_sdk/`.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `AGENTS.md`, `sdk/AGENTS.md`, `sdk/source_home.manifest.json`, `sdk/public-interface/README.md`.

## Boundaries

- Keep executable behavior in `src/aoa_sdk/`.
- Keep repeatable operation pressure in `mechanics/`.
- Keep public API posture tied to tests.
- Do not document a supported entrypoint that is not implemented.
- Do not turn typed models into sibling-source authority.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

State whether the change touched Python API posture, CLI posture, model
posture, implementation, or mechanic routes.
