# Plan Compilation Control Plane

## Role

This Boundary Bridge part implements C2 of the Agent OS control plane:
deterministic compilation of one resolved route and exact reviewed scenario
binding into a runtime-neutral `RunPlan`.

It consumes the admitted `aoa_playbook_plan_contour_v1` projection owned by
`aoa-playbooks`. It does not parse playbook prose, select a runtime adapter,
activate a capability, or execute a step.

## Inputs

- a resolved or degraded `RouteDecision` with one selected candidate;
- an exact `ScenarioBinding` containing the owner contour's agents,
  capabilities, expected artifacts, generic or kind-selected inputs, reviewed
  boolean conditions, and owner requirement references;
- a runtime-owner `RuntimeProfile` declaring compatibility, not authorization;
- the exact packaged contour/schema pin from
  `aoa-playbooks@056cac249a353ae94abedbd4048e6730f70c064d`;
- the latest eligible `playbook_registry_bundle` admission and materialized
  subject-store identity observed when that pin was created.

## Outputs

- one content-addressed `PlanSnapshot`;
- one immutable `RunPlan`;
- the owner contour's retained step order and dependencies;
- false guarded steps and guarded evidence/eval/retention requirements pruned
  without inventing replacement meaning;
- exact route approvals, owner references, input provenance, eval anchors,
  checkpoint, retry, rollback, evidence, retention, and closeout contours.

## Public routes

- Python: `AoASDK.control_plane.compile(decision, scenario, runtime_profile)`;
- CLI: `aoa route compile DECISION SCENARIO RUNTIME_PROFILE`;
- validation: `aoa route validate RUN_PLAN --against DECISION`.

## Next route

C3 implements `AoARunner.prepare()` and the verified lifecycle client over a
caller-supplied adapter. The SDK reference adapter executes no steps. C4 must
land a production adapter in the runtime owner's authority before any runtime
invocation claim.

## Validation

Use [VALIDATION.md](VALIDATION.md). Green C2 checks prove deterministic
compilation over the pinned contour and tested bindings. The installed-wheel
probe separately proves that package data and compilation work without an
`aoa-playbooks` checkout. These checks do not prove runtime invocation, task
benefit, cost reduction, consumer-zero, or archive readiness.
