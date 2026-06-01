# Checkpoint Parts

| Part | Role | Active payload |
| --- | --- | --- |
| `session-growth-checkpoint-cycle` | Capture, review, gate, and promote session-local checkpoint notes while staying below owner truth. | docs and `src/aoa_sdk/checkpoints/` route references |
| `reviewed-session-handoff-runner` | Build, queue, process, and report reviewed session handoff manifests without claiming owner truth. | docs, scripts, `src/aoa_sdk/closeout/`, and root integration tests |
| `child-task-reentry` | Build child-task summon, return, checkpoint bridge, and reviewed closeout helper packets. | docs, examples, tests, and `src/aoa_sdk/a2a/` route references |
| `reviewed-closeout-context-carry` | Keep reviewed closeout context maps, component-refresh hints, continuity hints, and next-kernel decisions advisory and schema-checked. | docs, schemas, examples, and tests |

Candidate-only checkpoint parts stay listed in `mechanics/checkpoint/PARTS.md`
until they have part-local payload.
