# Recurrence Hook Pack

This insert adds a third recurrence layer to `aoa-sdk`: thin hook-bound observation producers.

The hook pack does **not** mutate owner repos, run playbooks, or widen routing authority.
It only turns already-authored artifact families into `ObservationRecord` surfaces that can
flow into the beacon layer and candidate ledger.

## Purpose

The beacon wave can only see what it is fed.
This hook pack feeds it with bounded observations from four current artifact families:

- receipts
- description-trigger eval suites
- harvest and real-run notes
- runtime evidence-selection artifacts

## Core rule

Hooks here are observation producers, not orchestration authority.

They may:

- read current owner-authored artifact surfaces
- emit bounded observations
- preserve missing-path and warning visibility
- bridge stable session hooks into reviewable recurrence packets

They must not:

- auto-promote techniques
- auto-activate skills
- auto-create playbooks
- auto-author eval bundles
- act like a hidden scheduler

## First-wave producers

- `jsonl_receipt_watch`
- `skill_trigger_gap_watch`
- `harvest_pattern_watch`
- `runtime_candidate_watch`

Each producer is intentionally narrow and tied to a current artifact family instead of trying
to be a universal rule engine.

## Event posture

The current bridge target is the shared-root stable hook family:

- `session_start`
- `user_prompt_submit`
- `session_stop`

This wave seeds owner bindings on `session_stop` because that is the safest place to read
receipts, trigger refreshes, harvest notes, and runtime evidence without pretending that the
hook itself owns execution.

## Control-plane artifacts

- `schemas/hook_binding_set.schema.json`
- `schemas/hook_run_report.schema.json`
- `src/aoa_sdk/recurrence/hook_registry.py`
- `src/aoa_sdk/recurrence/hooks.py`

## CLI

```bash
aoa recur hooks list --event session_stop --root /srv/federation
aoa recur hooks run --event session_stop --root /srv/federation --json
aoa recur observe --hook-run /srv/federation/aoa-sdk/.aoa/recurrence/hooks/session_stop.latest.json --json
```

The last step keeps hook output subordinate to the existing observe -> beacon -> ledger path.
