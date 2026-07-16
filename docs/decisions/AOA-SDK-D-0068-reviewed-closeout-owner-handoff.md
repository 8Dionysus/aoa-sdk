# Reviewed Closeout Is an Owner Handoff

## Status

Accepted.

This decision supersedes the active cross-repository publisher runner recorded
by AOA-SDK-D-0043 and its source-topology split in AOA-SDK-D-0057. Their
historical queue and implementation rationale remain repository evidence; they
no longer justify SDK-owned owner publication, skill-kernel completion, or
derived stats refresh.

## Index Metadata

- Decision ID: AOA-SDK-D-0068
- Original date: 2026-07-15
- Surface classes: public API, checkpoint, closeout, owner boundary, compatibility
- SDK facets: reviewed evidence handoff, runtime session identity, child-task reentry
- Mechanic parents: checkpoint
- Guard families: owner authority, no invented execution, reviewed evidence, manual validation
- Posture: accepted

## Context

The SDK closeout runner expected a project-core skill kernel plus publisher
scripts in `aoa-skills`, `aoa-evals`, `aoa-techniques`, and `aoa-memo`. Those
active owner surfaces no longer exist. The runner therefore encoded a retired
skill family, wrote into sibling-owned runtime lanes, refreshed stats as a
side effect, and derived the "next skill" from receipt presence rather than an
executing host decision.

Manual checkpoint trials established a smaller valid operation: after human or
agent review, preserve the reviewed artifact, evidence refs, provisional
capability candidates, and exact owner routes in an SDK-local handoff. Do not
claim that a skill, workflow, publisher, progression model, or owner mutation
was executed.

## Options Considered

- Recreate the removed owner scripts and project-core kernel as SDK fixtures.
- Rename the old skills while retaining the cross-repository publisher runner.
- Retire the runner and consolidate its evidence-preservation role into the
  reviewed checkpoint closeout materializer.

## Decision

The SDK owns reviewed evidence materialization and routing metadata only.

- `checkpoint materialize-closeout-handoff` writes an SDK-local reviewed
  evidence bundle, materialization receipt, and owner-candidate handoff.
- mutable checkpoint context and materialization require a host-provided
  runtime session identity; the SDK does not create an unscoped session or
  attach quarantined legacy evidence implicitly.
- `workflow.operations.checkpoint-closeout` is a capability candidate whose
  execution belongs to the owner playbook and executing host.
- owner repositories admit, publish, validate, and promote their own material;
  the SDK does not call inferred sibling publishers or refresh owner stats.
- A2A return carries reviewed evidence and capability candidates back to the
  parent; it does not relaunch a named skill or prescribe a skill execution
  chain.
- Legacy closeout manifests and reports remain historical evidence. They are
  not accepted as active execution contracts.

Remove the public `CloseoutAPI`, `aoa closeout` command family, project-core
skill-kernel contracts, publisher runner, queue processor, and active
`reviewed-session-handoff-runner` mechanic. Do not retain compatibility aliases
that silently invoke the retired behavior.

## Rationale

Reviewed session evidence is not owner truth. A generic SDK cannot know that a
sibling publisher remains admitted, that one receipt proves a skill ran, or
that a missing skill should run next. Preserving evidence and exact candidate
routes is useful; simulating the vanished execution topology is harmful.

Consolidation also removes a second closeout authority. The playbook owner can
compose real owner actions, while the SDK stays a typed control-plane helper.

## Consequences

- Existing clients of `AoASDK.closeout` and `aoa closeout` must move to the
  reviewed checkpoint materialization route or invoke an owner workflow.
- Checkpoint lifecycle records materialization, not skill execution.
- Session-local evidence stays under the SDK session-growth area until review
  and archive; sibling repositories receive only explicitly accepted owner
  work through their own contracts.
- Permanent tests prove the manually observed no-execution and owner-boundary
  invariants instead of mocking removed publisher scripts.

## Source Surfaces

- `src/aoa_sdk/checkpoints/closeout/`
- `src/aoa_sdk/checkpoints/registry.py`
- `src/aoa_sdk/a2a/rebase/`
- `src/aoa_sdk/api.py`
- `src/aoa_sdk/cli/main.py`
- `mechanics/checkpoint/`

## Follow-Up Route

Route real reviewed checkpoint follow-through to
`workflow.operations.checkpoint-closeout`. Route bounded child-task execution
to `workflow.operations.delegation`. Let each downstream owner validate and
accept its own candidate without SDK-side publication.

## Verification

- manual host-runtime and legacy-evidence trials;
- manual review, materialization, lifecycle, and close/archive trial;
- absence check for retired owner publishers and project-core surfaces;
- focused checkpoint and A2A tests derived from those trials;
- decision indexes, mechanics topology, package, and release validation.
