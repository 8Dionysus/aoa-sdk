# Recurrence Hook Pack

This insert adds a third recurrence layer to `aoa-sdk`: thin hook-bound observation producers.

The hook pack does **not** mutate owner repos, run playbooks, or widen routing authority.
It only turns already-authored artifact families into `ObservationRecord` surfaces that can
flow into the beacon layer and candidate ledger.

## Purpose

The beacon layer can only see what it is fed.
This hook pack feeds it with bounded observations from three current artifact families:

- receipts
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

Technique-sensitive observations follow
[`technique-publication-observation-boundary.md`](technique-publication-observation-boundary.md):
publication, evidence, and review moments may emit observations, but they do not
authorize canonical technique status.

## Seed Producers

- `jsonl_receipt_watch`
- `harvest_pattern_watch`
- `runtime_candidate_watch`

Each producer is intentionally narrow and tied to a current artifact family instead of trying
to be a universal rule engine.

## Event posture

The current bridge target is the shared-root stable hook family:

- `session_start`
- `user_prompt_submit`
- `session_stop`

This route binds owner observations on `session_stop` because that is the safest place to read
receipts, trigger refreshes, harvest notes, and runtime evidence without pretending that the
hook itself owns execution.

## Control-plane artifacts

- `mechanics/recurrence/parts/hook-observation-pack/schemas/hook_binding_set.schema.json`
- `mechanics/recurrence/parts/hook-observation-pack/schemas/hook_run_report.schema.json`
- `mechanics/recurrence/parts/hook-observation-pack/docs/technique-publication-observation-boundary.md`
- `src/aoa_sdk/recurrence/hook_registry.py`
- `src/aoa_sdk/recurrence/hooks.py`

## CLI

Hook listing, bounded execution, and observation intake are owned by the
recurrence CLI. Exact operator and test routes live in the part
`VALIDATION.md`.

The last step keeps hook output subordinate to the existing observe -> beacon -> ledger path.
