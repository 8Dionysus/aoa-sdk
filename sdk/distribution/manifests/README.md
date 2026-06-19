# Distribution Manifests

This directory holds OS Abyss artifact bundle manifests for built SDK
distribution outputs.

The manifests are source inputs for `abyss-machine` artifact verification. They
identify the repo-local ABI identity, the built artifact subjects under
`dist/`, and the package metadata source used for SBOM and provenance sidecars.

Validation route:

```bash
python -m build
python mechanics/release-support/parts/release-audit-publish-helper/scripts/validate_abyss_machine_package_artifact_bundle.py
```

Generated sidecars are written under `dist/abyss-artifact-bundle/` and remain
ignored build output, not source truth.
