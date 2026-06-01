# Stress Posture Dispatch Gate

This part owns the SDK route from explicit stress context to a visible,
narrowing-only dispatch decision.

## Role

Input: caller-supplied stress context, source receipt refs, routing hint refs,
memo refs, degraded surface refs, and requested mutation posture.

Output: selected skill ids, blocked auto-activation reasons, required review
steps, and evidence refs that explain why mutation stayed gated.

Owner: `aoa-sdk` owns the typed control-plane carry and examples. Owner
repositories own degraded behavior and repair; `aoa-evals` owns proof wording;
`aoa-memo` owns durable memory.

## Active Surfaces

- [Stress Posture Dispatch Gate](docs/stress-posture-dispatch-gate.md)
- [Stress Posture Dispatch Request](examples/stress-posture-dispatch-request.example.json)
- [Stress Posture Dispatch Decision](examples/stress-posture-dispatch-decision.example.json)

## Next Route

Route proof questions to `aoa-evals`, durable lessons to `aoa-memo`, and
owner-local repair or runtime degradation to the affected owner repository.
