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
- an explicit selected `ScenarioRef` matching the admitted contour;
- an exact `ScenarioBinding` whose authored capability aliases are resolved
  through the same routing snapshot's pinned `aoa-skills` migration and
  capability graph, while required agents and eval/memo refs are read from
  their exact pinned owner Git objects;
- generic or kind-selected inputs and reviewed boolean conditions supplied by
  the caller rather than inferred by the SDK;
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

- Python: `AoASDK.control_plane.scenario_ref(scenario_id)`;
- Python: `AoASDK.control_plane.bind_scenario(decision, scenario_id, ...)`;
- Python: `AoASDK.control_plane.compile(decision, scenario, runtime_profile)`;
- CLI: `aoa route compile DECISION SCENARIO RUNTIME_PROFILE`;
- validation: `aoa route validate RUN_PLAN --against DECISION`.

The C1 entry capability remains in the route decision as navigation evidence.
It is not required to be a playbook DAG step. Each playbook requirement keeps
its authored alias alongside the resolved capability, semantic owner,
availability, lifecycle posture, and migration provenance. An `unbound`
runtime guard therefore remains visibly unbound; binding does not activate or
promote it.

## Next route

C3 implements `AoARunner.prepare()` and the verified lifecycle client over a
caller-supplied adapter. The SDK reference adapter executes no steps. C4 must
land a production adapter in the runtime owner's authority before any runtime
invocation claim.

## Validation

Use [VALIDATION.md](VALIDATION.md). Green C2 checks prove deterministic
compilation over the pinned contour and tested bindings. The base
installed-wheel probe proves packaged compilation without an
`aoa-playbooks` checkout. The public golden-chain verifier separately proves
live C1 resolution, exact owner binding, and C2 compilation for all three
admitted scenarios; it intentionally requires the pinned owner repositories.
The clean-federation wrapper repeats that chain with no `aoa-routing`
checkout.
These checks do not prove runtime invocation, task benefit, cost reduction,
consumer-zero, or archive readiness.
