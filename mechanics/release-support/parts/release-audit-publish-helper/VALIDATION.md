# Release Audit Publish Helper Validation

```bash
python -m pytest -q mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py
python mechanics/release-support/parts/release-audit-publish-helper/scripts/validate_abyss_machine_package_artifact_bundle.py
python scripts/release_check.py
```
