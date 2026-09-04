# Release Audit Publish Helper Validation

Repository-wide source-home, workspace-capsule, package-build, release, and full-suite checks are owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks) and [its release-facing lane](../../../../VALIDATION.md#release-facing-and-full-owner-checks).

```bash
python -m pytest -q mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py
python mechanics/release-support/parts/release-audit-publish-helper/scripts/validate_abyss_machine_package_artifact_bundle.py
```


Routing wheel verification is owned by [the consumed-surface posture gate](../../../boundary-bridge/parts/consumed-surface-posture-gate/VALIDATION.md), and plan wheel verification by [the plan compilation control plane](../../../boundary-bridge/parts/plan-compilation-control-plane/VALIDATION.md).
