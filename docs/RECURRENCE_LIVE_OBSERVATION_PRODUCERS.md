# Recurrence Live Observation Producers

This seed adds the first live producer layer for recurrence. It reads owner-authored artifact families and emits `ObservationRecord` / `ObservationPacket` surfaces for the existing `observe -> beacon -> ledger -> review` path.

The producers are not a scheduler, not an owner decision engine, and not an agent-spawn mechanism. They do not mutate canon, promote techniques, activate skills, author eval bundles, create playbooks, update KAG, or widen routing authority.

## Producers

- `generated_staleness_watch` compares source/contract/docs mtimes against generated surfaces declared by recurrence components.
- `technique_intake_watch` reads cross-layer technique candidate lanes such as future import, overlap hold, layer incubation, and not-yet-technique-shaped posture.
- `technique_readiness_watch` reads promotion readiness and canonical-pressure surfaces, including second-consumer/adopter pressure.
- `skill_trigger_surface_watch` reads description-trigger eval cases, collisions, manual invocation boundaries, and live skill receipts to emit omission/gap observations.
- `runtime_evidence_selection_watch` reads selected runtime evidence sidecars and promotion-guide boundaries without treating runtime posture as proof canon.
- `playbook_harvest_watch` reads real-run harvests, gate notes, fallback patterns, subagent mentions, and automation-seed pressure.
- `recurrence_event_repetition_watch` reads saved recurrence events to detect repeated changed/unmatched paths that may need owner law, a skill, a playbook, an eval, or a technique distillation.

## CLI

```bash
aoa recur live producers --root /srv/AbyssOS/workspace --json

aoa recur live observe \
  --root /srv/AbyssOS/workspace \
  --producer technique_readiness_watch \
  --producer skill_trigger_surface_watch \
  --json
```

Script fallback:

```bash
python scripts/collect_live_recurrence_observations.py \
  --workspace-root /srv/AbyssOS/workspace \
  --json
```

## Boundary

These producers only convert existing artifacts into observations. Beacon rules still decide whether observations become hints, watch items, candidates, or review-ready packets. Owner repos still make status decisions through their own review surfaces.
