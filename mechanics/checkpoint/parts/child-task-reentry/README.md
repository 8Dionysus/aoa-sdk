# Child-Task Reentry

## Role

Build bounded A2A child-task request, result, return, checkpoint-evidence,
memo, and reviewed owner-handoff packets without transferring owner authority
into SDK or claiming capability execution.

## Input

- SDK-owned bounded child-task request and result schemas
- quest passport, summon intent, stress, progression, and self-agent posture
- Codex-local projection manifest from `aoa-agents`
- reviewed child-task artifacts and checkpoint refs

## Output

- summon request/result payloads
- return plans and transition decisions
- checkpoint evidence-handoff plans and bundles
- reviewed evidence handoff requests
- runtime return evidence receipt candidates
- dry-run E2E fixture

## Owner

`aoa-sdk` owns its bounded child-task packet schemas and assembly.
`aoa-skills`, `aoa-agents`, `aoa-evals`, `aoa-memo`, `aoa-playbooks`,
`aoa-routing`, and `abyss-stack` keep domain authority.

## Next Route

Reviewed child-task material routes through checkpoint evidence
materialization, explicit owner handoff, memo writeback, eval proof, playbook
review, and routing re-entry.
