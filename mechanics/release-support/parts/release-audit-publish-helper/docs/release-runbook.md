# Release Audit Publish Helper Runbook

`aoa-sdk` publishes the control-plane release contract for the AoA federation.

Release work here stays bounded:

- the SDK does not author sibling meaning
- the SDK verifies and publishes release surfaces without inventing changelog prose
- release publication is only honest when repo state, tags, GitHub Releases, and README surfaces all agree

See also:

- `README.md`
- `mechanics/release-support/parts/public-support-ci-posture/docs/public-support-ci-posture.md`
- `docs/versioning.md`
- `CHANGELOG.md`

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
   - `aoa release audit /srv/AbyssOS --phase preflight --repo aoa-sdk --strict --json`
5. Merge the release-prep PR to `main`.
6. Publish through the bounded helper rather than ad-hoc shell steps:
   - dry run: `aoa release publish /srv/AbyssOS --repo aoa-sdk --dry-run --json`
   - real publish: `aoa release publish /srv/AbyssOS --repo aoa-sdk --confirm --json`
7. Re-run the postpublish audit:
   - `aoa release audit /srv/AbyssOS --phase postpublish --repo aoa-sdk --strict --json`

## Release contract

Preflight is red if any of these are false:

- `docs/RELEASING.md` exists as the repo-level preflight route to this part
- a repo-owned release verifier exists and passes at either
  `scripts/release_check.py` or `scripts/release_gate/release_check.py`
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

## Routing G5 candidate validation

The non-publishing routing-owner candidate extends the release battery with
focused source, typing, package, and installed-wheel checks:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_g5_candidate.py
python -m mypy src/aoa_sdk/control_plane/routing
python -m build
python mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_g5_candidate_wheel.py
python mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_g5_release_candidate_wheel.py
python mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_g5_canonical_wheel.py
```

These commands prove candidate construction and installed-package behavior.
They do not grant durable artifact admission, runtime cutover, G5, predecessor
retirement, compatibility-window start, or archival authority.

## Routing G5 release-candidate publication

The public release candidate is a separate trust stage, not the G5 switch:

```bash
python mechanics/release-support/parts/release-audit-publish-helper/scripts/build_routing_g5_release_candidate.py \
  --workspace-root /path/to/exact-input-worktrees \
  --sdk-root /path/to/exact-aoa-sdk-worktree \
  --predecessor-root /path/to/exact-aoa-routing-worktree \
  --output-dir /path/to/fresh/release-candidate \
  --archive-output /path/to/aoa-sdk-routing-g5-release-candidate-v0.7.0.tar.gz \
  --checksum-output /path/to/aoa-sdk-routing-g5-release-candidate-v0.7.0.tar.gz.sha256
```

The matching tag workflow checks out every input and the stronger-owner
verifier at the exact refs in
`sdk/distribution/manifests/routing_g5_release_candidate.input-lock.json`,
repeats package and envelope validation, resolves and hashes all 29 manifest
subjects through an explicit runtime `--subject-root`, attests the archive
digest through GitHub OIDC, and exports the archive, checksum, and verification
sidecars. The subject root is runtime-only and is not embedded as an absolute
public reference.

Publication is not complete until the exact archive is attached to the
matching GitHub Release and its public attestation verifies. Stronger-owner
promotion must then allow `release_consumer` and deny normal `runtime`.
Only the later separate G5 receipt may change canonical ownership.

If the original tag workflow fails before attestation because of a workflow,
runner, or carrier-determinism defect, do not move or recreate the public tag.
Land the bounded orchestration repair on `main`, then dispatch `Release
Artifacts` from that repaired workflow with `release_tag` set to the existing
exact tag. The workflow checks out that immutable tag for the repository
package and nested SDK producer input, rebuilds the same subject bytes, and
uses a separate checkout of the reviewed workflow revision only for replay
orchestration and canonical archive encoding. GitHub attestation provenance
records that tooling revision separately. A replay must reject non-semantic
tag names and must not substitute current `main` as the release source or
input lock.

## Routing G5 canonical publication

`v0.8.0` is the separate owner-switch release. It consumes the immutable
`v0.7.0` release candidate as a byte-parity trust root and adds the
owner-switch receipt without changing any of its 27 routing assembly members:

```bash
python mechanics/release-support/parts/release-audit-publish-helper/scripts/build_routing_g5_canonical.py \
  --workspace-root /path/to/exact-input-worktrees \
  --sdk-root /path/to/exact-aoa-sdk-worktree \
  --predecessor-root /path/to/exact-aoa-routing-worktree \
  --public-release-archive /path/to/aoa-sdk-routing-g5-release-candidate-v0.7.0.tar.gz \
  --runtime-consumer-root /path/to/abyss-stack-at-fac82c75 \
  --output-dir /path/to/fresh/canonical \
  --archive-output /path/to/aoa-sdk-routing-g5-canonical-v0.8.0.tar.gz \
  --checksum-output /path/to/aoa-sdk-routing-g5-canonical-v0.8.0.tar.gz.sha256
```

The exact inputs, public asset digest, runtime contract, compatibility start,
and authority flags are pinned in
`sdk/distribution/manifests/routing_g5_canonical.input-lock.json`. The tag
workflow downloads and verifies the public asset, rebuilds the canonical
envelope twice, verifies its checksum, and attests the new archive.

This release makes `aoa-sdk` the canonical routing producer. It does not
pretend the downstream steps already ran: canonical provenance keeps
`live_cutover_executed=false`, and the receipt keeps
`archive_authorized=false`. `abyss-machine` admission, the separate
`abyss-stack` cutover receipt, the paired predecessor M3 record, compatibility
exit, consumer-zero, and archive approval remain ordered follow-ups.

## Notes

- `aoa release publish` may create or update the annotated tag and the GitHub Release, but it must not invent versions or prose.
- The GitHub Release highlights come only from `### Summary` bullets in the latest tagged changelog section.
- Cadence debt is surfaced separately through `aoa release audit /srv/AbyssOS --phase cadence --all --json`.
