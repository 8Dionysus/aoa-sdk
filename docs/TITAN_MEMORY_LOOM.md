# Titan Memory Loom

The Memory Loom is a local-first cross-session index for Titan service-cohort work.

It ingests receipts and events into candidate-grade records, supports recall queries, creates derived digests, and preserves redaction/tombstone trails.

## CLI

```bash
python scripts/titan_memory_loom.py init --workspace /srv/AbyssOS --operator Dionysus --out /srv/AbyssOS/.titan/memory/index.json
python scripts/titan_memory_loom.py event --index /srv/AbyssOS/.titan/memory/index.json --titan Mneme --kind note --text "A seed landed."
python scripts/titan_memory_loom.py recall --index /srv/AbyssOS/.titan/memory/index.json --query seed
python scripts/titan_memory_loom.py digest --index /srv/AbyssOS/.titan/memory/index.json
python scripts/titan_memory_loom.py redact --index /srv/AbyssOS/.titan/memory/index.json --record-id <id> --reason "operator requested mask"
python scripts/titan_memory_loom.py close --index /srv/AbyssOS/.titan/memory/index.json
```

## Authority

Every recall result is advisory. Treat it as a route to sources, not the source itself.
