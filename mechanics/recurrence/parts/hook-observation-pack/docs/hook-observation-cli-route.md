# Hook Pack Insert

This route extends the recurrence seed with hook-bound observation producers.

## What changes

- new hook binding schema
- new hook run report schema
- hook registry loader
- three seed producers
- CLI bridge under `aoa recur hooks ...`
- owner hook binding sets for `aoa-techniques`, `aoa-evals`, and `aoa-playbooks`

## Why This Route Exists

Beacon rules are only as good as their observations.
The hook pack gives the beacon layer a narrow, reviewable feed from the artifact families
that most often reveal growth pressure:

- techniques through receipts
- playbooks through harvest and real-run patterns
- evals through bounded runtime evidence selection

## Boundary to preserve

This insert adds observation producers only.
It does not add live scheduling, automatic playbook execution, or agent autonomy.
Skill-use evidence routes through session memory and explicit owner review; the
hook pack does not infer invocation or omission.
