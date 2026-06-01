# Public Support CI Posture Validation

```bash
python -m pytest -q mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py mechanics/release-support/parts/public-support-ci-posture/tests/test_sibling_canary.py tests/test_docs_routes.py
python mechanics/release-support/parts/public-support-ci-posture/scripts/run_sibling_canary.py --repo-root . --repo aoa-skills --format json
python scripts/validate_mechanics_topology.py
```
