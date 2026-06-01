# Runtime Mirror Boundary

## Role

`runtime-mirror-boundary` verifies that live workspace reads distinguish source
checkouts from deployed runtime mirrors and report missing future surfaces
honestly.

## Input

- live workspace discovery
- workspace config patterns
- compatibility surface requirements
- source checkout versus runtime mirror candidates

## Output

- source-preferred path selection
- compatible/missing/incompatible surface reports
- explicit missing-future-surface posture

## Owner

`aoa-sdk` owns the SDK read boundary. Host deployment and runtime mirror
population remain outside SDK truth.

## Validation

Use `VALIDATION.md`.
