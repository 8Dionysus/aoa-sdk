# Graph CLI Route

Snapshot, closure, and diff entrypoints are owned by the recurrence CLI under
`src/aoa_sdk/recurrence/cli_graph.py`. Their executable operator and test route
is `../VALIDATION.md`.

The snapshot/diff commands are read-only. The closure command is also read-only and exists to expose transitive blast radius before planner/review work.
