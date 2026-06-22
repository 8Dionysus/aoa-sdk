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
`dist/abyss-artifact-registry/`, materializes the package subject store, checks
consumer `trust-gate` admission, and rehearses adversarial failures for missing
SBOM, wrong SLSA subject binding, private path leakage, unverified latest
registration, and revoked records.

Use that part when changing release audit, publish helper behavior, changelog
publication shape, or release validation.
