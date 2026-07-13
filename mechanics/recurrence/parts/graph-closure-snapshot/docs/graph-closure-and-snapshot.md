# Recurrence graph closure and snapshot

This part hardens recurrence from direct edge walking into typed graph closure. It preserves the old `expand_component_graph` seam so the existing planner can keep calling it, but the return now carries depth, lineage, edge strength, cycles, skipped edges, and external impacts.

## Law

- The graph is advisory/control-plane, not a new owner of meaning.
- Component manifests remain source-authored.
- Closure may reveal cycles and blind edges, but it does not mutate surfaces.
- Snapshots are memory of shape, not verdicts.
- Deltas are review input for Codex and owner maintainers.

## Executable route

Snapshot, closure, diff, and snapshot-builder entrypoints are owned by the
recurrence CLI and part-local script. Exact operator and test routes live in
`../VALIDATION.md`.

## What changed

- `graph.py` now exposes transitive closure with depth limits and cycle detection.
- `planner.py` writes `batch_order`, `graph_depth`, `edge_strength`, and `propagation_batches`.
- `GraphSnapshot` records component nodes and typed consumer edges.
- `GraphDeltaReport` compares snapshots and reports added/removed/changed nodes and edges.

## Stop-lines

This part does not launch agents, run proof operations, promote techniques,
update KAG, or turn routing into graph authority.
