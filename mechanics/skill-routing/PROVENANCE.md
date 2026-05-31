# Skill Routing Provenance

## Source Surfaces

- `.agents/skills/`
- `docs/skill-runtime-recommendation-gap.md`
- `docs/skill-runtime-recommendation-gap-fix-spec.md`
- `src/aoa_sdk/skills/`
- `tests/test_skills.py`
- `tests/test_skill_reference_contracts.py`

## Stronger Owners

`aoa-skills` owns skill meaning. The SDK owns bounded local wrappers over
published skill exports.

## Notes

This is SDK-local because it is the consumer-side skill route, not the shared
skill doctrine package.
