# A2A Child-Task Return And Owner Handoff

This part is the `aoa-sdk` control-plane boundary for a bounded child task. It
owns the request and result packet schemas under `schemas/`; it does not own
the meaning or execution of the capabilities named by those packets.

## Owner boundaries

- `aoa-sdk` owns packet assembly, return planning, reviewed evidence carrying,
  and exact owner-route metadata.
- `aoa-agents` owns Codex role projection defaults. The SDK may read its
  projection manifest when building a local target.
- `aoa-kag` and the executing runtime own semantic retrieval, compatibility
  reasoning, and task-local DAG construction.
- playbook, eval, memo, routing, runtime, and skill owners admit and execute
  their own work. An SDK handoff is only a reviewed candidate.

## Packet chain

1. A request carries one or more exact `capability_refs`, a bounded passport,
   expected outputs, and audit references.
2. The SDK assesses transport and control posture without selecting a skill.
3. A failed or regrounding child produces a return plan. When checkpoint
   evidence exists, its next hop is the capability
   `workflow.operations.checkpoint-closeout`, not a skill name.
4. A checkpoint evidence-handoff bundle preserves the reviewed artifact,
   provisional capability candidates, and session refs.
5. Explicit owner handoffs identify who may accept each candidate and which
   evidence must be reviewed.

No step invokes an owner publisher, runs a skill, or claims that the named
capability executed. Result packets, checkpoint bundles, reviewed return
handoffs, and runtime evidence candidates all keep
`capability_execution_claimed=false`.

## Dry-run fixture

`sdk.a2a.build_summon_return_checkpoint_fixture()` generates
`examples/summon_return_checkpoint_e2e.fixture.json`. The fixture joins the
SDK-owned request/result schemas, exact capability refs, Codex-local target,
reviewed child result, return plan, checkpoint evidence, memo candidate, owner
handoffs, runtime evidence candidate, and routing re-entry pointer. It remains
`dry_run=true` and `live_automation=false`.

The fixture is a reviewable contract example, not evidence that any owner
accepted or executed its candidate.
