# AGENTS.md

## Applies to

`mechanics/codex-projection/parts/`.

## Role

Route functioning Codex Projection parts that own SDK-local Codex-facing
control-plane artifacts while keeping runtime and rollout authority outside the
SDK.

## Relevant routes

The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/codex-projection/AGENTS.md`, `mechanics/codex-projection/PARTS.md`, `README.md`, `CONTRACT.md`, `VALIDATION.md`.

## Boundaries

- Stay on the control plane.
- Do not make SDK readouts a Codex runtime or deploy authority.
- Keep external rollout artifact names as compatibility inputs, not active SDK
  route names.
- Do not add a functioning part without local contract and validation docs.

## Closeout

Report which part moved root payload, which external owner tokens remain as
compatibility inputs, and which validation commands ran.
