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

For an external owner, add this manifest field and replace the placeholders
with the exact pinned SDK source values before running the command:

```json
"runner_pin": {
  "schema_version": "aoa_validation_runner_pin_v1",
  "owner_repo": "aoa-sdk",
  "relative_path": "mechanics/release-support/parts/validation-evidence-graph/scripts/validation_graph.py",
  "source_commit": "<40-or-64-lowercase-hex-git-id>",
  "file_sha256": "sha256:<64-lowercase-hex-digest>"
}
```

The SDK-local manifest uses `null` because its owner root and runner source
checkout are the same. Missing or mismatched pins, or a changed inherited
environment digest, make the receipt insufficient.

Owner and topology checks:

```bash
python /srv/AbyssOS/aoa-evals/scripts/validate_local_eval_port.py --target-root .
python scripts/validate_mechanics_topology.py
```
