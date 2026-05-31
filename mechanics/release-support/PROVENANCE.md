# Release Support Provenance

## Source Surfaces

- `CHANGELOG.md`
- `docs/RELEASING.md`
- `docs/RELEASE_CI_POSTURE.md`
- `.github/workflows/repo-validation.yml`
- `scripts/release_check.py`
- `src/aoa_sdk/release/`
- `tests/test_release.py`
- `tests/test_roadmap_parity.py`

## Stronger Owners

GitHub, package publication targets, and sibling repositories own actual
publication state. SDK release support owns checks and dry-run helpers.

## Notes

This shared mechanic name matches the refactored AoA release-support package
pattern while keeping publication truth external until verified.
