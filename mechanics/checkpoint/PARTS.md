# Checkpoint Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| session-growth-checkpoint-cycle | `parts/session-growth-checkpoint-cycle/`, `parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/`, `src/aoa_sdk/checkpoints/`, part-local checkpoint API/CLI tests | captures and reviews session-local evidence, materializes reviewed closeout handoffs, and manages lifecycle movement without minting capability execution or owner truth |
| child-task-reentry | `mechanics/checkpoint/parts/child-task-reentry/docs/summon-return-checkpoint.md`, `mechanics/checkpoint/parts/child-task-reentry/docs/return-reentry.md`, `src/aoa_sdk/a2a/` | carries child-task return packets back below owner acceptance |
| reviewed-closeout-context-carry | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/` | active; carries reviewed maps, component-refresh hints, continuity hints, and next-kernel decisions below owner truth |
