# Child-Task Reentry

## Role

Build bounded A2A child-task summon, return, checkpoint bridge, memo handoff,
and reviewed closeout packets without transferring owner authority into SDK.

## Input

- `aoa-skills` summon request and result schemas
- quest passport, summon intent, stress, progression, and self-agent posture
- Codex-local projection manifest from `aoa-agents`
- reviewed child-task artifacts and checkpoint refs

## Output

- summon request/result payloads
- return plans and transition decisions
- checkpoint bridge plans and context bundles
- reviewed closeout requests
- runtime return closeout receipt candidates
- dry-run E2E fixture

## Owner

`aoa-sdk` owns packet assembly and compatibility with the sibling contracts.
`aoa-skills`, `aoa-agents`, `aoa-evals`, `aoa-memo`, `aoa-playbooks`,
`aoa-routing`, and `abyss-stack` keep domain authority.

## Next Route

Reviewed child-task material routes through checkpoint closeout, owner
publication, memo writeback, eval proof, playbook review, and routing re-entry.
