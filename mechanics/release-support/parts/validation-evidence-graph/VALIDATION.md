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

Default repo-wide gate and exact rollback:

```bash
python scripts/release_check.py --receipt /tmp/aoa-sdk-validation-receipt.json
python scripts/release_check.py --mode serial
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
python scripts/validate_mechanics_topology.py
```
