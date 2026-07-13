# Titan Memory Loom

The Memory Loom is a local-first cross-session index for Titan service-cohort work.

It ingests receipts and events into candidate-grade records, supports recall queries, creates derived digests, and preserves redaction/tombstone trails.

## CLI

Initialization, event intake, recall, digest, redaction, and close behavior are
owned by the part-local `scripts/titan_memory_loom.py`. Canonical operator and
regression routes are in `../VALIDATION.md`.

## Authority

Every recall result is advisory. Treat it as a route to sources, not the source itself.
