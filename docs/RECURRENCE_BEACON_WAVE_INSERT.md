# Recurrence Beacon Wave Insert

Use this note when planting the emergence side of recurrence.

## Minimal landing sequence

1. land the updated `models.py`, `api.py`, `cli.py`, and `io.py`
2. add `observations.py`, `beacons.py`, `ledger.py`, and `usage_gaps.py`
3. add the new schemas and examples
4. plant the four owner manifests for:
   - `aoa-techniques`
   - `aoa-skills`
   - `aoa-evals`
   - `aoa-playbooks`
5. keep the existing first-wave manifests for `8Dionysus` and `aoa-agents`
6. run the repo-local validators and tests

## Suggested first command chain

```bash
aoa recur detect /path/to/repo --path docs/TRIGGER_EVALS.md --json
aoa recur observe --signal /path/to/signal.json --supplemental /path/to/extra-observations.json --json
aoa recur beacon /path/to/observations.json --json
aoa recur ledger /path/to/beacons.json --candidates-only --json
aoa recur usage-gaps /path/to/beacons.json --json
```

## Practical rule

Start with one real signal source and one manual supplemental packet.

Do not wait for perfect automation. A stable packet shape now is more valuable than a mythical final hook matrix later.
