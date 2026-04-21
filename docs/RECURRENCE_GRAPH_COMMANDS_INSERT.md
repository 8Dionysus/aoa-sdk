# Insert: graph commands

Add this to `RECURRENCE_CONTROL_PLANE.md` near the existing recurrence command list.

```bash
aoa recur graph snapshot --root /srv/workspace --json
aoa recur graph closure --root /srv/workspace --component component:<owner>:<name> --depth-limit 8 --json
aoa recur graph diff .aoa/recurrence/graph-snapshots/before.json .aoa/recurrence/graph-snapshots/after.json --json
```

The snapshot/diff commands are read-only. The closure command is also read-only and exists to expose transitive blast radius before planner/review work.
