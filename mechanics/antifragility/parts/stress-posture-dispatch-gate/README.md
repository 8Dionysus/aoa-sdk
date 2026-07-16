# Stress Posture Dispatch Gate

This part owns the SDK route from caller-supplied typed stress signals to a
visible, narrowing-only task-dispatch decision.

## Role

Input: `StressSignal` values with explicit source family, posture, severity,
evidence refs, blocked actions, and re-entry conditions.

Output: a merged `StressBundle` and an optional `SummonDecision` whose posture,
blocked actions, reason codes, and evidence refs explain why task dispatch was
narrowed or gated.

Owner: `aoa-sdk` owns typed control-plane carry, task-dispatch constraints, and
examples. `aoa-skills` owns skill bundles and capability relations; KAG owns
semantic retrieval and composition; host runtimes own execution. Owner
repositories own degraded behavior and repair; `aoa-evals` owns proof wording;
`aoa-memo` owns durable memory.

## Active Surfaces

- [Stress Posture Dispatch Gate](docs/stress-posture-dispatch-gate.md)
- [Stress Posture Dispatch Request](examples/stress-posture-dispatch-request.example.json)
- [Stress Posture Dispatch Decision](examples/stress-posture-dispatch-decision.example.json)

## Next Route

Route proof questions to `aoa-evals`, durable lessons to `aoa-memo`, and
owner-local repair or runtime degradation to the affected owner repository.
Route skill discovery and composition to the `aoa-skills` owner surfaces and
KAG instead of interpreting stress as a skill-selection request.
