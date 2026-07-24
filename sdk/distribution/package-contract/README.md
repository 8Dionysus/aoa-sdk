# Package Contract

Role: route package metadata, build shape, and import distribution promises.

Input: `pyproject.toml`, package name/version posture, build metadata,
included source files, packaged routing schemas, and import-surface
distribution expectations.

Output: package metadata update, build validation, OS Abyss artifact bundle
sidecars for built wheel/sdist outputs, release-support route, or decision
record.

Owner: `sdk/distribution/AGENTS.md` and
`sdk/source_home.manifest.json#package_contract`.

Next route: `pyproject.toml`, `src/aoa_sdk/`,
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_shadow_wheel.py`,
`sdk/distribution/manifests/python_distribution.bundle.json`,
`mechanics/release-support/parts/release-audit-publish-helper/`, and the
package build owner in `pyproject.toml`.

Stop line: do not claim package publication before external publication proof
exists, and do not claim the routing shadow is distributable until an installed
wheel reproduces and validates its fourteen artifacts and sidecar.
