# Graph Closure Snapshot Validation

```bash
python mechanics/recurrence/parts/graph-closure-snapshot/scripts/build_recurrence_graph_snapshot.py --workspace-root /srv/AbyssOS --skip-manifest-diagnostics --json
python -m pytest -q mechanics/recurrence/parts/graph-closure-snapshot/tests/test_recurrence_graph_closure_snapshot_seed.py
```
