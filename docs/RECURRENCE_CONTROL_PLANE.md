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
- `aoa-routing` may later consume thin return hints, but recurrence does not move into routing
- `aoa-kag` may later consume regrounding obligations, but recurrence does not make KAG a graph sovereign
- `aoa-agents` will later act on this seam, but agents are not introduced in wave one

## Owner contract

Each owner repo may plant manifests under:

```text
manifests/recurrence/*.json
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

## Wave-one commands

```bash
aoa recur detect /srv/8Dionysus --from git:HEAD~1..HEAD --root /srv --json
aoa recur plan /srv/aoa-sdk/.aoa/recurrence/signals/8Dionysus.latest.json --root /srv --json
aoa recur doctor /srv/aoa-sdk/.aoa/recurrence/signals/8Dionysus.latest.json --root /srv --json
aoa recur handoff /srv/aoa-sdk/.aoa/recurrence/plans/component.codex-plane.shared-root.latest.json --reviewed --root /srv --json
```

## Honesty rules

Wave one must not:

- mutate owner repos on detection
- claim validation already passed when only a plan exists
- convert unresolved downstream edges into fake certainty
- pretend recurrence is complete while target manifests are still missing
- introduce hidden scheduler authority
