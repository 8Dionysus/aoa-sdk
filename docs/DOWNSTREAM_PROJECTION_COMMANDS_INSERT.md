# CLI insert: downstream recurrence projections

Add a `project` sub-command group under `aoa recur`.

```bash
aoa recur project routing --root /srv/AbyssOS/workspace --json
aoa recur project stats --root /srv/AbyssOS/workspace --json
aoa recur project kag --root /srv/AbyssOS/workspace --json
aoa recur project build --root /srv/AbyssOS/workspace --json
```

Primary inputs are optional so Codex can run the pack incrementally during landing:

- `--plan`
- `--doctor`
- `--handoff`
- `--beacon`
- `--review-queue`
- `--review-summary`
- `--decision-report`

The `build` command persists both the bundle and the guard report.
