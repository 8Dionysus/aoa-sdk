# AoA Surface Detection Boundary

Surface detection is a read-only SDK control-plane seam. It turns explicit
intent and bounded deterministic signals into owner-surface candidates without
selecting, loading, or executing a skill.

## Boundary

- `aoa surfaces detect` may emit `candidate-now` or `candidate-later` items.
- Every item has `executable_now=false`.
- An explicit `skill` request points to
  `aoa-skills.agent_skill_catalog`; it is not a dispatch result.
- The detector does not read installed user or repository skills, skill
  runtime sessions, activation logs, or session receipts.
- `phase=checkpoint` may create session-local checkpoint candidates, but it
  does not promote them into an owner repository.
- `aoa surfaces handoff` requires an explicit reviewed route.

## Inputs and output

The detector uses intent, phase, mutation posture, optional current
`aoa-routing.owner_layer_shortlist.min` hints, and bounded stats re-grounding
signals. It emits schema-v2 `SurfaceDetectionReport` objects with candidates,
owner refs, ambiguity, inspection gaps, and checkpoint carry.

Reports persist only as session-local control-plane evidence under:

```text
aoa-sdk/.aoa/surface-detection/{label}.{phase}.latest.json
```

That location is not owner truth. `aoa-skills`, each repository home, KAG, and
the host retain their own source, retrieval, projection, and execution roles.

## Truth rules

- Filesystem presence is not selection or execution.
- A routing shortlist is advisory and stale skill refs are reported as gaps.
- A session receipt cannot upgrade a candidate or modify an owner surface.
- Capability targets in reviewed handoff packets are refs, not invocations.

Use `surface-detection-heuristics.md` for the bounded signal map,
`surface-detection-enrichment.md` for advisory context, and
`surface-closeout-handoff.md` for reviewed handoff behavior.
