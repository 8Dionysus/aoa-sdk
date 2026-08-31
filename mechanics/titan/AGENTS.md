# AGENTS.md

## Applies to

`mechanics/titan/`.

## Role

Route the shared Titan mechanic for SDK helper contracts around incarnation,
runtime receipts, operator console, appserver bridge, memory loom, visible
session replay, and swarm closeout.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/titan/README.md`, `mechanics/titan/ROADMAP.md`, `mechanics/titan/PARTS.md`, `mechanics/titan/PROVENANCE.md`, `mechanics/titan/parts/`, `src/aoa_sdk/titans/`.

## Boundaries

- Stay on the control plane.
- Keep active Titan artifacts under `mechanics/titan/parts/<part>/`.
- Do not turn SDK Titan helpers into Titan runtime, role, identity, or memory authority.
- Do not turn SDK Titan helpers into operator authority.
- Keep launch, approval, replay, recall, and closeout artifacts explicit and
  inspectable.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report which Titan helper route changed and which runtime, memory, proof, or
owner authority remains outside SDK.
