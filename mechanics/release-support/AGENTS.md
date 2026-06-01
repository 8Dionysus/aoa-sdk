# AGENTS.md

## Applies to

`mechanics/release-support/`.

## Role

Route the shared release-support mechanic for changelog, release audit, CI
posture, build, publication helper, and Repo Validation support.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/release-support/README.md`
- `mechanics/release-support/parts/AGENTS.md`
- `mechanics/release-support/parts/release-audit-publish-helper/README.md`
- `mechanics/release-support/parts/public-support-ci-posture/README.md`
- `CHANGELOG.md`
- `docs/RELEASING.md`
- `docs/RELEASE_CI_POSTURE.md`
- `scripts/release_check.py`
- `src/aoa_sdk/release/`

## Boundaries

- Stay on the control plane.
- Do not make release helper output a GitHub Release or package publication.
- Keep sibling release truth in sibling repositories.
- Keep changelog claims tied to validation evidence.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python scripts/release_check.py
python -m pytest -q mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py
```

## Closeout

Report release-facing surfaces changed and the exact validation gate that ran.
