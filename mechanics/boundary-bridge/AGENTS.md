# AGENTS.md

## Applies to

`mechanics/boundary-bridge/`.

## Role

Route the shared boundary-bridge mechanic for typed SDK facades that keep SDK
handles separate from sibling-owned meaning.

## Relevant routes

The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/boundary-bridge/README.md`, `mechanics/boundary-bridge/ROADMAP.md`, `mechanics/boundary-bridge/parts/AGENTS.md`, `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/README.md`, `mechanics/boundary-bridge/parts/skill-environment-inspector/README.md`, `docs/boundaries.md`, `src/aoa_sdk/*/registry.py`, `src/aoa_sdk/routing/`, `src/aoa_sdk/skills/`.

## Boundaries

- Stay on the control plane.
- Do not make a facade a source owner.
- Preserve truth labels and owner return routes.
- Keep skill environment inspection below owner meaning and do not select,
  dispatch, or claim capability execution.
- Keep sibling policy, proof, memory, role, and routing meaning outside SDK
  source truth.

## Validation

Validation for Boundary Bridge paths belongs to the nearest active bridge part `VALIDATION.md`; broader checks inherit root `VALIDATION.md`.

## Closeout

Report which facade or bridge changed and which sibling owner still owns
meaning.
