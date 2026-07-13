# Recurrence Control Plane

The recurrence control plane gives `aoa-sdk` one programmable control-plane seam.

The seam is narrow on purpose:

- detect changed source or deployed surfaces
- match them against source-authored recurrence manifests
- build an ordered propagation plan
- expose connectivity gaps instead of hiding them
- emit one reviewed return handoff
- stop before mutation

## Governing split

- source repos own meaning and refresh law
- `aoa-sdk` owns typed recurrence carry, matching, planning, and reviewed handoff packets
- `aoa-routing` may consume thin owner, return, and gap hints, but recurrence does not move into routing
- `aoa-stats` may consume derived counts and pressure summaries, but recurrence does not create verdict authority there
- `aoa-kag` may consume regrounding obligations, but recurrence does not make KAG a graph sovereign
- `aoa-agents` may act on reviewed handoff surfaces, but agents are not introduced by this SDK seam

## Owner contract

Each owner repo may plant manifests under:

```text
mechanics/recurrence/manifests/**/*.json
mechanics/recurrence/parts/*/manifests/**/*.json
manifests/recurrence/*.json
manifests/recurrence/**/*.json
```

A recurrence manifest names:

- one `component_ref`
- source inputs
- generated and projected surfaces
- contract, docs, test, and receipt surfaces
- explicit refresh routes
- downstream consumer edges
- rollback anchors
- drift signals and freshness posture

## Manifest compatibility gate

The registry is tolerant at the scan boundary and strict at the load boundary.
It recursively scans recurrence manifest districts, loads only
`recurrence_component` manifests, and keeps hook, review, rollout, wiring, and
Agon-shaped observation manifests as diagnostics instead of trying to coerce
them into components.

Run the gate before graph closure, observation producers, or downstream
projection work. The executable scan and validator routes are owned by the
recurrence CLI, the part-local validator, and this part's `VALIDATION.md`.

`adapter_required` Agon diagnostics are observation-only. They must not create
arena sessions, verdicts, scars, ranks, owner mutations, or agent spawns.
High or critical diagnostics remain blocking compatibility issues.

## Graph closure and snapshots

After the manifest gate is clean enough to load components, recurrence graph
inspection is still read-only. Closure exposes transitive blast radius, depth,
edge strength, cycles, skipped edges, external impacts, and topological
propagation batches before planner or review work. Snapshots record graph shape
for comparison; deltas are review input, not routing authority.

Snapshot, closure, diff, and snapshot building are owned by the graph-closure
part and its `VALIDATION.md`.

## Control-plane route

Manifest, graph, live-observation, review, projection, detection, planning,
doctor, and reviewed-handoff command families are owned by the recurrence CLI.
Each part's `VALIDATION.md` owns its exact focused checks; root `AGENTS.md`
owns the repository-wide executable route.

## Honesty rules

This control plane must not:

- mutate owner repos on detection
- claim validation already passed when only a plan exists
- convert unresolved downstream edges into fake certainty
- pretend recurrence is complete while target manifests are still missing
- introduce hidden scheduler authority
- publish downstream generated projection surfaces when the projection guard reports blocked or critical violations
