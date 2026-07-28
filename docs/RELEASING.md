# Release Route

This root file is the repo-level release preflight door required by federation
release audit. It is not the full runbook.

Active release-support runbook:

- `mechanics/release-support/parts/release-audit-publish-helper/docs/release-runbook.md`

The release preflight also verifies the built wheel and sdist through
`mechanics/release-support/parts/release-audit-publish-helper/scripts/validate_abyss_machine_package_artifact_bundle.py`,
which writes OS
Abyss ABI, SBOM, SLSA/in-toto, signature-decision, and verify sidecars under
ignored `dist/abyss-artifact-bundle/`.
The same helper writes the local bundle registry under
`dist/abyss-artifact-registry/`, promotes durable evidence with host-managed
trust-root metadata, materializes the package subject store under
`dist/abyss-artifact-subjects/`, checks consumer `trust-gate` admission, and
rehearses adversarial failures for missing SBOM, wrong SLSA subject binding,
private path leakage, unverified latest registration, and revoked records.

For `v0.7.0`, the release battery also produces the exact public routing G5
release-candidate archive from the pinned input lock, verifies it with the
pinned `abyss-machine` source, and attests its digest. This establishes release
trust only: `aoa-routing` remains canonical and normal runtime remains denied
until the separate G5 receipt.

For `v0.8.0`, the battery reconstructs those exact public routing bytes,
requires byte-for-byte parity, adds the G5 owner-switch receipt and canonical
provenance, and attests a separate canonical archive. This authorizes
`aoa-sdk` as producer but records live runtime cutover as unexecuted and keeps
archive authority false.

After G5, ordinary SDK releases do not rebuild the M1 shadow, G5 candidate, or
G5 release-candidate envelopes and do not checkout `aoa-routing`. Those
immutable stages remain replayable historical evidence. The active release
battery verifies the canonical SDK routing wheel, C2 plan compiler, C3 Runner,
C5 evidence chain, and package trust bundle.

Use that part when changing release audit, publish helper behavior, changelog
publication shape, or release validation.
