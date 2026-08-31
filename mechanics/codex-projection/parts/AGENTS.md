# AGENTS.md

## Applies to

`mechanics/codex-projection/parts/`.

## Role

Route functioning Codex Projection parts that own SDK-local Codex-facing
control-plane artifacts while keeping runtime and rollout authority outside the
SDK.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/codex-projection/AGENTS.md`, `mechanics/codex-projection/PARTS.md`, `README.md`, `CONTRACT.md`, `VALIDATION.md`.

## Boundaries

- Stay on the control plane.
- Do not make SDK readouts a Codex runtime or deploy authority.
- Keep external rollout artifact names as compatibility inputs, not active SDK
  route names.
- Do not add a functioning part without local contract and validation docs.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report which part moved root payload, which external owner tokens remain as
compatibility inputs, and which validation commands ran.
