# AGENTS.md

## Applies to

`mechanics/titan/`.

## Role

Route the shared Titan mechanic for SDK helper contracts around incarnation,
runtime receipts, operator console, appserver bridge, memory loom, visible
session replay, and swarm closeout.

## Relevant routes

The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/titan/README.md`, `mechanics/titan/ROADMAP.md`, `mechanics/titan/PARTS.md`, `mechanics/titan/PROVENANCE.md`, `mechanics/titan/parts/`, `src/aoa_sdk/titans/`.

## Boundaries

- Stay on the control plane.
- Keep active Titan artifacts under `mechanics/titan/parts/<part>/`.
- Do not turn SDK Titan helpers into Titan runtime, role, identity, or memory authority.
- Do not turn SDK Titan helpers into operator authority.
- Keep launch, approval, replay, recall, and closeout artifacts explicit and
  inspectable.

## Validation

Validation for Titan paths belongs to the nearest active Titan part `VALIDATION.md`; broader checks inherit root `VALIDATION.md`.

## Closeout

Report which Titan helper route changed and which runtime, memory, proof, or
owner authority remains outside SDK.
