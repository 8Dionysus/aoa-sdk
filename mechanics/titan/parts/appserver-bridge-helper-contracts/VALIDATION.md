# Appserver Bridge Helper Contracts Validation

For edits to this helper or its tests, run the complete local behavior suite
without discovering unrelated installed pytest plugins:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q mechanics/titan/parts/appserver-bridge-helper-contracts/tests/test_titan_appserver_bridge.py
python mechanics/titan/parts/appserver-bridge-helper-contracts/scripts/titan_appserver_bridge.py --help
```

This suite uses pytest's built-in fixtures and retains its real CLI subprocess
checks and negative approval/gate cases. No worker pool or result cache is
needed. Omit the environment assignment for the ordinary plugin-enabled
comparison; suites that require external plugins must load those explicitly
or retain their own normal command. The full owner gate is unchanged.

For automatic test-territory selection from an edit to this part:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python scripts/release_check.py --feedback --changed-path mechanics/titan/parts/appserver-bridge-helper-contracts/scripts/titan_appserver_bridge.py
```

This executes the same four tests, including CLI behavior; an observed complete
selection/startup/test cycle took 0.51 s. Source-family edits select the broader
mechanic, and unknown/shared paths expand to the full graph. Supply every
changed path; this contextual feedback does not replace full release checks.

Ten alternating paired runs on a shared development host on 2026-09-04,
each in a fresh Python process and with the same four passing tests, measured
median whole-command wall time of 1.48 s with plugin discovery and 0.70 s
without it (maximum 1.81 s and 0.90 s). Median child CPU was 1.32 s and
0.57 s. These are local observations, not a system-wide p95 or a cold-disk
guarantee. The comparison disabled pytest's cache provider in both methods;
that cache is not needed for correctness and may remain enabled for everyday
failed-test reruns.

After correcting a failure, pytest can give immediate focused feedback:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q --lf mechanics/titan/parts/appserver-bridge-helper-contracts/tests/test_titan_appserver_bridge.py
```

This selects the last failing tests, not every consumer of changed code. Run
the complete local command above after that feedback, and widen to other
affected parts for shared changes; this is not cached owner-gate acceptance.
A temporary wrong-gate mutation was detected by the complete local suite in
0.71 s, and the restored source passed the failed-test rerun in 0.33 s. The
mutation was removed and no production behavior was changed.

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
