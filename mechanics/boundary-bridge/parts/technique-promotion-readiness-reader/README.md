# Technique Promotion Readiness Reader

## Role

`technique-promotion-readiness-reader` is the Boundary Bridge part that verifies
the SDK facade for `aoa-techniques` promotion-readiness readouts.

## Input

- consumed surface `aoa-techniques.technique_promotion_readiness.min`
- workspace discovery and compatibility loading
- `src/aoa_sdk/techniques/` importable source

## Output

- `TechniquesAPI.promotion_readiness(...)` typed read behavior
- regression coverage for canonical and promoted technique entries

## Owner

`aoa-sdk` owns typed access and validation of the reader. `aoa-techniques` owns
technique meaning, promotion readiness, canonical status, blockers, and review
authority.

## Next Route

If the readout shape or compatibility contract drifts, update the
`aoa-techniques` source surface first, then the SDK compatibility/read facade.

## Validation

Use `VALIDATION.md`.
