# Technique Promotion Readiness Reader Contract

## Contract

The part reads the generated `aoa-techniques` promotion-readiness surface
through the SDK compatibility loader and returns typed SDK models. It is a
reader and boundary bridge, not a technique distillation, promotion, or review
surface.

## SDK-Owned Active Names

- part route: `boundary-bridge/technique-promotion-readiness-reader`
- source module: `src/aoa_sdk/techniques/`
- test route: `tests/test_technique_promotion_readiness_reader.py` inside this part

## External Compatibility Inputs

- `aoa-techniques.technique_promotion_readiness.min`
- `generated/technique_promotion_readiness.min.json` in the `aoa-techniques`
  owner checkout or fixture

## Stop-Lines

- Do not promote, canonicalize, suppress, or review techniques in `aoa-sdk`.
- Do not keep this single-facade regression in root `tests/`.
- Do not make SDK model truth stronger than the owner `aoa-techniques` surface.
