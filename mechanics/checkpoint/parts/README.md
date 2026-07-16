# Checkpoint Parts

| Part | Role | Active payload |
| --- | --- | --- |
| `session-growth-checkpoint-cycle` | Capture, review, materialize, and archive session-local checkpoint evidence while staying below capability execution and owner truth. | docs and `src/aoa_sdk/checkpoints/` route references |
| `child-task-reentry` | Build bounded child-task request, return, checkpoint-evidence, and reviewed owner-handoff packets. | docs, schemas, examples, tests, and `src/aoa_sdk/a2a/` route references |
| `reviewed-closeout-context-carry` | Keep reviewed closeout context maps, component-refresh hints, continuity hints, and next-kernel decisions advisory and schema-checked. | docs, schemas, examples, and tests |

Candidate-only checkpoint parts stay listed in `mechanics/checkpoint/PARTS.md`
until they have part-local payload.
