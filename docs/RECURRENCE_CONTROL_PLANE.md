# Recurrence Control Plane

First-wave recurrence gives `aoa-sdk` one new programmable control-plane seam.

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
- `aoa-agents` will later act on this seam, but agents are not introduced in wave one

## Owner contract

Each owner repo may plant manifests under:

```text
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
It recursively scans `manifests/recurrence/**/*.json`, loads only
`recurrence_component` manifests, and keeps hook, review, rollout, wiring, and
Agon-shaped observation manifests as diagnostics instead of trying to coerce
them into components.

Run the gate before graph closure, observation producers, or downstream
projection work:

```bash
aoa recur manifest-scan --root /srv/AbyssOS --json
python scripts/validate_recurrence_manifests.py --workspace-root /srv/AbyssOS
```

`adapter_required` Agon diagnostics are observation-only. They must not create
arena sessions, verdicts, scars, ranks, owner mutations, or agent spawns.
High or critical diagnostics remain blocking compatibility issues.

## Graph closure and snapshots

After the manifest gate is clean enough to load components, recurrence graph
inspection is still read-only. Closure exposes transitive blast radius, depth,
edge strength, cycles, skipped edges, external impacts, and topological
propagation batches before planner or review work. Snapshots record graph shape
for comparison; deltas are review input, not routing authority.

```bash
aoa recur graph snapshot --root /srv/AbyssOS --json
aoa recur graph closure --root /srv/AbyssOS --component component:<owner>:<name> --depth-limit 8 --json
aoa recur graph diff before.snapshot.json after.snapshot.json --root /srv/AbyssOS --json
python scripts/build_recurrence_graph_snapshot.py --workspace-root /srv/AbyssOS --json
```

## Wave-one commands

```bash
aoa recur manifest-scan --root /srv/AbyssOS --json
aoa recur graph snapshot --root /srv/AbyssOS --json
aoa recur graph closure --root /srv/AbyssOS --component component:<owner>:<name> --depth-limit 8 --json
aoa recur graph diff before.snapshot.json after.snapshot.json --root /srv/AbyssOS --json
aoa recur live producers --root /srv/AbyssOS --json
aoa recur live observe --root /srv/AbyssOS --json
aoa recur review decision-template /srv/AbyssOS/aoa-sdk/.aoa/recurrence/review-queues/latest.json --item-ref review-item:0001 --decision defer --root /srv/AbyssOS --json
aoa recur review close /srv/AbyssOS/aoa-sdk/.aoa/recurrence/review-queues/latest.json --decision /srv/AbyssOS/aoa-sdk/.aoa/recurrence/review-decisions/decision.example.json --root /srv/AbyssOS --json
aoa recur project routing --root /srv/AbyssOS --json
aoa recur project stats --root /srv/AbyssOS --json
aoa recur project kag --root /srv/AbyssOS --json
aoa recur project build --root /srv/AbyssOS --json
aoa recur detect /srv/AbyssOS/8Dionysus --from git:HEAD~1..HEAD --root /srv/AbyssOS --json
aoa recur plan /srv/AbyssOS/aoa-sdk/.aoa/recurrence/signals/8Dionysus.latest.json --root /srv/AbyssOS --json
aoa recur doctor /srv/AbyssOS/aoa-sdk/.aoa/recurrence/signals/8Dionysus.latest.json --root /srv/AbyssOS --json
aoa recur handoff /srv/AbyssOS/aoa-sdk/.aoa/recurrence/plans/component.codex-plane.shared-root.latest.json --reviewed --root /srv/AbyssOS --json
```

## Honesty rules

Wave one must not:

- mutate owner repos on detection
- claim validation already passed when only a plan exists
- convert unresolved downstream edges into fake certainty
- pretend recurrence is complete while target manifests are still missing
- introduce hidden scheduler authority
- publish downstream generated projection surfaces when the projection guard reports blocked or critical violations
