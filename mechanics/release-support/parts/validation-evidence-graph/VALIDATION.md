# Validation Evidence Graph Validation

Fast contract check:

```bash
python mechanics/release-support/parts/validation-evidence-graph/scripts/validation_graph.py --profile instant
python -m pytest -q mechanics/release-support/parts/validation-evidence-graph/tests/test_validation_graph.py
```

Full owner-local evidence graph:

```bash
python mechanics/release-support/parts/validation-evidence-graph/scripts/validation_graph.py --profile full --receipt /tmp/aoa-sdk-validation-receipt.json
```

The full command preserves every `scripts/release_check.py` obligation. The
temporary receipt path is illustrative; CI should use its runner-managed
temporary directory and retain the receipt even on failure.

The ordinary test node uses two pytest-xdist workers with `loadfile`: each
file and its module fixtures stay together. The separately isolated G11 nodes
and every other graph obligation remain unchanged. This adds no new runner;
the retained serial oracle still executes without xdist. For focused tests,
use the relevant part's serial command instead of paying worker startup cost.

Matched full ordinary-suite observations on a shared development host:
serial 50.63 s wall / 34.14 s CPU, two workers 20.08 s / 36.61 s,
four workers 13.29 s / 46.58 s. Each selected 889 passing tests, two existing
skips and 537 passing subtests. These are single-run comparisons, not p95 or
hosted-CI guarantees. Two workers keep total CPU near serial while other graph
nodes run concurrently. Four remain useful when wall time outweighs contention:

```bash
python -m pytest -q -n 4 --dist loadfile --ignore=evals/suites/test_agent_os_control_plane_g11.py
```

Default repo-wide gate and exact rollback:

```bash
python scripts/release_check.py --receipt /tmp/aoa-sdk-validation-receipt.json
AOA_SDK_VALIDATION_MODE=serial python scripts/release_check.py
```

The first command always requests the full owner claim set. The latter two
commands execute the retained serial completeness oracle; they are rollback
and comparison routes, not weaker profiles.

Explicit sibling-owner ABI check from a pinned `aoa-sdk` source checkout:

```bash
python /path/to/pinned-aoa-sdk/mechanics/release-support/parts/validation-evidence-graph/scripts/validation_graph.py \
  --repo-root /path/to/owner-repo \
  --manifest /path/to/owner-repo/path/to/validation_graph.json \
  --profile full \
  --receipt /tmp/owner-validation-receipt.json
```

The manifest must live inside the explicit owner root. The receipt binds that
owner Git identity and the pinned SDK runner Git identity separately. This
invocation shares scheduling mechanics only; it does not import SDK claims or
authorize the sibling gate.

Owner and topology checks:

```bash
python /srv/AbyssOS/aoa-evals/scripts/validate_local_eval_port.py --target-root .
```

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).

Serial completeness is owned by [the root serial lane](../../../../VALIDATION.md#serial-completeness-and-rollback).
