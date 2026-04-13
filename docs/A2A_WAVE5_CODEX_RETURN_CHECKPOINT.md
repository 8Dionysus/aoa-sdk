# A2A Wave 5 Codex / Return / Checkpoint Slice

This note records the current control-plane helper slice for A2A-related work in `aoa-sdk`.

## What this slice may build

- Codex-local child targets
- summon decisions that respect passport, stress, progression, and self-agent posture
- return plans
- `transition_decision` payloads for return
- checkpoint bridge plans
- reviewed closeout requests
- reviewed memo export plans
- owner-local publication plans

## What it must not do

- auto-run skill meaning
- auto-run reviewed closeout reasoning
- invent new owner-local receipt families
- replace workspace install truth
- replace role, playbook, memo, or eval ownership

## Practical posture

For current local bounded work, the helper slice should prefer `codex_local` unless the caller explicitly needs remote transport.

When a child route degrades, the helper slice should plan:

1. return
2. optional checkpoint bridge context
3. reviewed closeout request
4. owner-local publication

That keeps the control plane sharp without turning the SDK into a shadow runtime.
