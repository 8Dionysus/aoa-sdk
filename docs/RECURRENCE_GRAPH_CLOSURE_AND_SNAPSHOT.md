# Recurrence graph closure and snapshot

This seed hardens recurrence from direct edge walking into typed graph closure. It preserves the old `expand_component_graph` seam so the existing planner can keep calling it, but the return now carries depth, lineage, edge strength, cycles, skipped edges, and external impacts.

## Law

- The graph is advisory/control-plane, not a new owner of meaning.
- Component manifests remain source-authored.
- Closure may reveal cycles and blind edges, but it does not mutate surfaces.
- Snapshots are memory of shape, not verdicts.
- Deltas are review input for Codex and owner maintainers.

## Commands

```bash
aoa recur graph snapshot --root /srv/workspace --json
aoa recur graph closure --root /srv/workspace --component component:skills:activation-boundary --json
aoa recur graph diff before.snapshot.json after.snapshot.json --root /srv/workspace --json
python scripts/build_recurrence_graph_snapshot.py --workspace-root /srv/workspace --json
```

## What changed

- `graph.py` now exposes transitive closure with depth limits and cycle detection.
- `planner.py` writes `batch_order`, `graph_depth`, `edge_strength`, and `propagation_batches`.
- `GraphSnapshot` records component nodes and typed consumer edges.
- `GraphDeltaReport` compares snapshots and reports added/removed/changed nodes and edges.

## Stop-lines

This seed does not launch agents, does not run proof commands, does not promote techniques, does not update KAG, and does not turn routing into graph authority.
