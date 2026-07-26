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
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_g5_candidate_wheel.py`,
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_g5_release_candidate_wheel.py`,
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_g5_canonical_wheel.py`,
`mechanics/boundary-bridge/parts/plan-compilation-control-plane/scripts/verify_plan_compilation_wheel.py`,
`sdk/distribution/manifests/python_distribution.bundle.json`,
`mechanics/release-support/parts/release-audit-publish-helper/`, and the
package build owner in `pyproject.toml`.

Stop line: do not claim package publication before external publication proof
exists, and do not claim the routing shadow is distributable until an installed
wheel reproduces and validates its fourteen artifacts and sidecar. Do not
claim G5 from an installed candidate: it must keep all switch-authority flags
false until stronger-owner trust, runtime canary, rollback, and exact receipt
evidence pass. A public release-candidate archive and attestation establish
release trust only; normal runtime and canonical ownership remain separately
gated. A successful C2 wheel probe proves packaged plan-contour availability
and deterministic compilation, not adapter selection or runtime execution.
