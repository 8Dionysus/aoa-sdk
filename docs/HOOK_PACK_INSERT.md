# Hook Pack Insert

This wave extends the recurrence seed with hook-bound observation producers.

## What changes

- new hook binding schema
- new hook run report schema
- hook registry loader
- four first-wave producers
- CLI bridge under `aoa recur hooks ...`
- owner hook binding sets for `aoa-techniques`, `aoa-skills`, `aoa-evals`, and `aoa-playbooks`

## Why this wave exists

Beacon rules are only as good as their observations.
The hook pack gives the beacon layer a narrow, reviewable feed from the artifact families
that most often reveal growth pressure:

- techniques through receipts
- skills through trigger suites and recent skill evidence
- playbooks through harvest and real-run patterns
- evals through bounded runtime evidence selection

## Boundary to preserve

This insert adds observation producers only.
It does not add live scheduling, automatic playbook execution, or agent autonomy.
