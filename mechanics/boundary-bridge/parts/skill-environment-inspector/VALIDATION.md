# Skill Environment Inspector Validation

Manual trials are the behavioral authority. Re-run current-owner, missing,
drifted, duplicate-scope, unadmitted-repository, legacy-workspace, exact-node,
and environment-override trials before changing the contract.

For home-port changes, also inspect v2/v3 owner homes, empty and foreign
exposures, subset selections, missing/symlinked source references, and a
same-name Codex user/repository conflict. Preserve the v1 public constructor
and repository projection checks. Structural foreign-exposure acceptance is
not evidence of another runtime executing the skill.

The retained regression checks cover only the invariants established by those
trials:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector.py mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector_cli.py
```

For current-host parity, also inspect the live user root with `aoa skills
inspect` and verify prompt visibility separately through the host runtime.

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
