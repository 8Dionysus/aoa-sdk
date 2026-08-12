# Compile obligation actor plans without selecting meaning

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0099
- Original date: 2026-08-11
- Surface classes: public API, plan compilation, runtime boundary, actor handoff
- SDK facets: control-plane, plan compilation, incarnation binding
- Mechanic parents: boundary-bridge
- Guard families: owner provenance, exact binding, no execution, effect ceiling
- Posture: accepted

## Context

The first evidence-complete external actor was compiled by a task-local Python
program that manually constructed `ScenarioBinding`, `PlanSnapshot`,
`RunPlan`, and their evidence requirements. That proved the runtime contour,
but every future obligation would have to repeat a large SDK object graph even
after `aoa-agents`, `aoa-models`, the domain owner, and the runtime owner had
already made and content-addressed their decisions.

The existing C2 compiler remains tied to an admitted `aoa-playbooks` contour.
An obligation-derived actor instead receives its choreography from an exact
task-local DAG and must not require a permanent playbook merely to materialize
one already-decided role-bearing duty.

## Options Considered

- Keep the object construction task-local for every external actor.
- Let `abyss-stack` infer and build the SDK plan while preparing a launch.
- Add a narrow SDK helper that consumes exact selected owner refs and emits a
  runtime-neutral obligation-actor plan without routing or execution.

## Decision

Expose `build_obligation_actor_run_plan` from the SDK control plane. The caller
must supply the exact task-local DAG, role, task request, all owner inputs,
runtime profile, ABI refs, named outputs, effect class, producer, checkpoint,
rollback, closeout, and compiler provenance.

The helper validates those relationships, creates one single-step plan, and
computes the canonical snapshot and plan digests. It admits only `read_only`
and `repo_mutation`; external effects remain outside this surface.

It performs no obligation detection, role or model selection, model-fit
interpretation, runtime selection, permission grant, launch, or acceptance.

## Rationale

The SDK owns typed control-plane construction, while every semantic choice
remains visible in a stronger-owner ref. Moving repeated object assembly here
lets a role-first coordinator remain small and inspectable without giving the
runtime or a hidden adapter authority over actor meaning.

## Consequences

- Future eval, stats, memo, landing, and other duties can share one SDK plan
  compiler without sharing a permanent domain workflow.
- The task-local DAG and domain procedure remain explicit inputs rather than
  SDK-owned meaning.
- Callers still must obtain and verify all owner refs before compilation.
- The returned plan is not an incarnation, host admission, launch, proof,
  owner acceptance, or model-fit verdict.

## Source Surfaces

- `src/aoa_sdk/control_plane/incarnation.py`
- `src/aoa_sdk/control_plane/__init__.py`
- `mechanics/boundary-bridge/parts/agent-incarnation-binding/`

## Follow-Up Route

Use this helper from the role-first `aoa-agents`/`aoa-summon` preparation
surface, then bind the exact plan through incarnation v2 and give only the
resulting complete packet to the `abyss-stack` external CLI runtime.

## Verification

Run the agent-incarnation part tests, public import checks, lint, type checks,
mechanics topology validation, decision-index parity, and the repository
release gate. Pair SDK proof with runtime-owner integration; an SDK plan does
not prove a process ran.
