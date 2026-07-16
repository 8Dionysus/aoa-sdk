# Runtime Entry

`sdk/runtime-entry/` owns SDK route posture for entry surfaces that touch local
workspace context, Codex orientation, or reviewed closeout flow.

## Families

| Family | Role | Next route |
| --- | --- | --- |
| `workspace-context/` | workspace root and mirror boundary posture | `.aoa/workspace.toml`, `src/aoa_sdk/workspace/`, runtime-seam mechanics |
| `codex-entrypoints/` | Codex-facing orientation posture | `src/aoa_sdk/codex/`, codex-projection mechanics |
| `closeout-entrypoints/` | checkpoint review and evidence-materialization posture | `src/aoa_sdk/checkpoints/`, `src/aoa_sdk/a2a/`, checkpoint mechanics |

## Stop Lines

- Runtime entry is not runtime authority.
- Checkpoint and closeout artifacts stay below capability execution and owner truth.
- Workspace discovery must stay explicit and testable.
