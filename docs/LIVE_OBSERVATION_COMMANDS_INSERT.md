# CLI insert: live observation producers

Add the `live` sub-application under `aoa recur`:

```bash
aoa recur live producers --root /srv/AbyssOS/workspace --json
aoa recur live observe --root /srv/AbyssOS/workspace --json
aoa recur live observe --producer generated_staleness_watch --producer runtime_evidence_selection_watch --json
```

Recommended pipeline after landing:

```bash
aoa recur live observe --root /srv/AbyssOS/workspace --json > /tmp/live-observations.json
aoa recur beacon /tmp/live-observations.json --root /srv/AbyssOS/workspace --json > /tmp/live-beacons.json
aoa recur review-queue /tmp/live-beacons.json --root /srv/AbyssOS/workspace --json
```

The commands are read-only except for writing recurrence output packets under `.aoa/recurrence` or the explicit `--report-output` path.
