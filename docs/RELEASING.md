# Releasing `aoa-sdk`

`aoa-sdk` publishes the control-plane release contract for the AoA federation.

Release work here stays bounded:

- the SDK does not author sibling meaning
- the SDK verifies and publishes release surfaces without inventing changelog prose
- release publication is only honest when repo state, tags, GitHub Releases, and README surfaces all agree

See also:

- [README](../README.md)
- [Release And CI Posture](RELEASE_CI_POSTURE.md)
- [Surface Versioning Policy](versioning.md)
- [CHANGELOG](../CHANGELOG.md)

## Release goals

A release should make it easy to answer:

- what changed in the SDK control plane
- why the version is honest
- how repo-local validation and federation release audit were both checked
- what remains outside SDK ownership

## Recommended release flow

1. Confirm the release scope stays on the control plane.
2. Update `CHANGELOG.md` and keep the latest tagged section in the `Summary / Validation / Notes` shape.
3. Run the bounded repo release battery:
   - `python scripts/release_check.py`
4. Run the federation preflight audit from the workspace root:
   - `aoa release audit /srv --phase preflight --repo aoa-sdk --strict --json`
5. Merge the release-prep PR to `main`.
6. Publish through the bounded helper rather than ad-hoc shell steps:
   - dry run: `aoa release publish /srv --repo aoa-sdk --dry-run --json`
   - real publish: `aoa release publish /srv --repo aoa-sdk --confirm --json`
7. Re-run the postpublish audit:
   - `aoa release audit /srv --phase postpublish --repo aoa-sdk --strict --json`

## Release contract

Preflight is red if any of these are false:

- `docs/RELEASING.md` exists
- `scripts/release_check.py` exists and passes
- tracked worktree is clean
- local `main` is synced with `origin/main`
- README shows the exact current-release banner
- the latest tagged changelog section has `Summary`, `Validation`, and `Notes`
- `pyproject.toml` and `src/aoa_sdk/cli/main.py` agree with the latest release version

Postpublish is red if any of these are false:

- the matching remote tag exists
- the matching GitHub Release exists
- the matching GitHub Release is marked latest
- the GitHub Release body keeps the canonical shape:
  - `Released`
  - `Canonical changelog`
  - `## Highlights`
  - `## Full Release Notes`
- `origin/main:README.md` still shows the same current-release banner

## Notes

- `aoa release publish` may create or update the annotated tag and the GitHub Release, but it must not invent versions or prose.
- The GitHub Release highlights come only from `### Summary` bullets in the latest tagged changelog section.
- Cadence debt is surfaced separately through `aoa release audit /srv --phase cadence --all --json`.
