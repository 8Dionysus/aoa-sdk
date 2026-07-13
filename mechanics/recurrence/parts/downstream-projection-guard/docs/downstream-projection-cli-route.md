# Downstream Recurrence Projection CLI Route

The recurrence CLI owns bounded routing, stats, KAG, and complete-bundle
projection modes. Their executable definitions remain under
`src/aoa_sdk/recurrence/`; focused checks are routed through
`../VALIDATION.md`.

Primary inputs are optional so a reviewed projection can be assembled
incrementally:

- `--plan`
- `--doctor`
- `--handoff`
- `--beacon`
- `--review-queue`
- `--review-summary`
- `--decision-report`

The `build` command persists both the bundle and the guard report.
