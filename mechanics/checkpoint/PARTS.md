# Checkpoint Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| session-growth-checkpoint-cycle | `parts/session-growth-checkpoint-cycle/`, `parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/`, `src/aoa_sdk/checkpoints/`, part-local checkpoint API/CLI tests | captures, reviews, gates, promotes session-local checkpoint notes, and carries managed Git boundary hook templates without minting owner truth |
| reviewed-session-handoff-runner | `parts/reviewed-session-handoff-runner/`, `parts/reviewed-session-handoff-runner/closeout-inbox-user-units/`, `src/aoa_sdk/closeout/`, part-local runner API/CLI tests | packages and runs reviewed session material without turning it into memory, proof, or owner verdict |
| child-task-reentry | `mechanics/checkpoint/parts/child-task-reentry/docs/summon-return-checkpoint.md`, `mechanics/checkpoint/parts/child-task-reentry/docs/return-reentry.md`, `src/aoa_sdk/a2a/` | carries child-task return packets back below owner acceptance |
| reviewed-closeout-context-carry | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/` | active; carries reviewed maps, component-refresh hints, continuity hints, and next-kernel decisions below owner truth |
