# AGENTS.md

## Applies To

This card applies to `sdk/runtime-entry/`.

## Role

`sdk/runtime-entry/` names Workspace, Codex, explicit Runner, and reviewed
closeout entry posture.

It keeps entry surfaces below runtime authority. The SDK may inspect, build
packets, coordinate a typed lifecycle through a caller-supplied adapter,
materialize reviewed evidence, or orient Codex; it must not become a runtime
worker.

## Relevant routes

The conditional references retained from this card are: `AGENTS.md`, `sdk/AGENTS.md`, `sdk/source_home.manifest.json`, `sdk/runtime-entry/README.md`, `.aoa/AGENTS.md`.

## Boundaries

- Do not make path guessing stronger than `.aoa/workspace.toml`.
- Do not turn Codex orientation into a Codex runtime.
- Do not treat checkpoint or closeout artifacts as memory, proof, progression,
  or owner verdicts.
- Do not create hidden daemon behavior from entrypoint posture.
- Do not discover or select a runtime adapter implicitly.
- Do not treat reference-adapter lifecycle events as plan-step execution.

## Closeout

State whether the route changed workspace context, Codex entry posture,
closeout entry posture, implementation, or mechanic validation.
