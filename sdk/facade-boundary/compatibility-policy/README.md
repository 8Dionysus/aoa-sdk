# Compatibility Policy

Role: route compatibility posture that keeps consumed surfaces explicit and
drift-visible.

Input: supported paths, sibling canary posture, compatibility checks, version
rules, and stale path removal.

Output: compatibility implementation route, release-support route, decision
record, or sibling-owner handoff.

Owner: `sdk/facade-boundary/AGENTS.md` and
`sdk/source_home.manifest.json#compatibility_policy`.

Next route: `src/aoa_sdk/compatibility/`,
`src/aoa_sdk/control_plane/routing/` for the pre-G5 non-publishing shadow
compiler, `docs/versioning.md`,
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`, and
`mechanics/release-support/parts/public-support-ci-posture/`.

Stop line: do not turn missing source surfaces into silent pass conditions,
and do not treat shadow generation as canonical publication or G5 authority.
