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

Owner and topology checks:

```bash
python /srv/AbyssOS/aoa-evals/scripts/validate_local_eval_port.py --target-root .
python scripts/validate_mechanics_topology.py
```
