# Owner-Layer Signal Handoff

## Role

Expose advisory owner-layer surface detection and reviewed closeout handoff
without turning hints into executable truth.

## Input

- `sdk.surfaces.detect(...)` reports
- `aoa surfaces detect` persisted reports
- reviewed session or checkpoint context
- sibling-owned shortlist, stats, and receipt context reads

## Output

- `SurfaceDetectionReport`
- `SurfaceCloseoutHandoff`
- reviewed handoff targets for session-growth or owner follow-through

## Owner

`aoa-sdk` owns the bridge shape and handoff packet. Sibling repos own the
meaning of skills, evals, memo, playbooks, agents, techniques, stats, and
routing.

## Next Route

Reviewed survivors route to checkpoint closeout, owner repos, or sibling
readers. They do not auto-activate here.
