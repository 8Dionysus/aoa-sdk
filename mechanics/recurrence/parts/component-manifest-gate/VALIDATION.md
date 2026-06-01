# Component Manifest Gate Validation

```bash
python mechanics/recurrence/parts/component-manifest-gate/scripts/validate_recurrence_manifests.py --workspace-root /srv/AbyssOS --json
python -m pytest -q mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_registry.py mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_seed.py mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_hardening_compat_seed.py
```
