# Session Growth Checkpoint Cycle Validation

Repository-wide source-home, workspace-capsule, package-build, release, and full-suite checks are owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks) and [its release-facing lane](../../../../VALIDATION.md#release-facing-and-full-owner-checks).

Run:

```bash
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_lifecycle_indexes.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_session_memory.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_candidate_intelligence.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_carrier_intelligence.py
```

For lifecycle audit and close/archive compatibility, also run:

```bash
aoa checkpoint backlog-audit /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --write-index --json
aoa checkpoint close-archive /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json
aoa checkpoint reconcile-sessions /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json
aoa checkpoint sweep-closed-sessions /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json
```

For candidate-intelligence navigation and generated index coverage, also run:

```bash
aoa checkpoint candidate-intelligence /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --sample-limit 3 --write-index --json
aoa checkpoint carrier-intelligence /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --sample-limit 3 --write-index --json
```

The cross-part control-plane routing suite is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#cross-part-routing-suites).

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
