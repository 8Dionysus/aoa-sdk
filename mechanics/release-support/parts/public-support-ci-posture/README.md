# Public Support CI Posture

This part owns the public support and CI-tier posture for SDK release claims.

## Role

Input: supported SDK claim pressure, release semantics, CI tier expectations,
and public onboarding route needs.

Output: a short posture document that names what the SDK can honestly support,
what it must not claim, and which checks reinforce a claim.

Owner: `aoa-sdk` owns public release/support posture. Sibling repositories own
their source meanings and release truth.

## Active Surfaces

- [Public Support CI Posture](docs/public-support-ci-posture.md)
- `docs/RELEASE_CI_POSTURE.md`
- [Sibling Canary Matrix](config/sibling_canary_matrix.json)
- [Sibling Canary Runner](scripts/run_sibling_canary.py)
- [Sibling Canary Tests](tests/test_sibling_canary.py)
- `.github/workflows/`
- `scripts/release_check.py`

## Next Route

Route changed source meaning to the owner repository before the SDK claims
support for reading, validating, or publishing that surface.
