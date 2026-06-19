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

Use that part when changing release audit, publish helper behavior, changelog
publication shape, or release validation.
