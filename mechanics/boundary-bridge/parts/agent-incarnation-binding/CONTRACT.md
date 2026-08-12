# Agent Incarnation Binding Contract

## SDK owns

- byte-compatible `aoa_agent_incarnation_binding_v1` historical-read shape;
- required `aoa_agent_incarnation_binding_v2` obligation, mandate,
  role-resolution, fit-query-result, fit-projection, realization, runtime, and
  canonical-digest chain for new external actors;
- exact cross-object validation against one `RunPlan`;
- validation of the plan snapshot and plan canonical digest before the
  incarnation can rely on its plan ref;
- an owner-subordinate loader that hashes one `aoa-models` realization without
  interpreting its fit claims;
- explicit permission, tool, observe-only usage metering, stop, continuation, wake, correlation,
  provenance, and return-owner fields;
- rejection of owner drift, unpinned inputs, role mismatch, effect-ceiling
  widening, implicit user config, and false continuation.
- deterministic compilation of one already-decided obligation actor into a
  runtime-neutral single-step `RunPlan`, with exact task request, task-local
  DAG, role, owner inputs, outputs, runtime profile, ABI, checkpoint, rollback,
  and closeout refs;
- an owner-subordinate loader that hashes and projects the exact
  `abyss-stack_external_codex_agent_v1` runtime descriptor without selecting a
  model or interpreting its model-admission entries;
- compatibility validation for generic execution postures only. Domain task
  families such as landing, eval, stats, or memo remain owner/runtime labels
  and are not enumerated or selected by the SDK adapter.

## Stronger owner split

- `aoa-agents` owns role and mandate meaning;
- `aoa-models` owns realization and model-claim meaning;
- `aoa-playbooks` owns scenario choreography;
- `abyss-stack` or another selected runtime owner owns tools, launch, process,
  session, events, resume, and execution evidence;
- `aoa-evals` owns comparison and verdict meaning;
- the target owner and human approval route own acceptance and effects.

## Admission order

```text
RunPlan
  + exact task request
  + exact role contract
  + exact model realization
  + exact runtime/tool profile
  + exact workspace source
  + bounded permission plus observe-only metering, stop and wake policies
  -> AgentIncarnationBindingV2 for a new external actor
  -> AgentIncarnationBinding only when reading historical v1 evidence
  -> runtime-owner delivery binding
```

The SDK binds refs; it does not select the model, launch a process, infer a
model-fit claim, or grant an effect.

The obligation-plan helper is not a second route resolver or playbook owner.
It accepts only already-selected refs and rejects external effects, empty or
duplicate outputs, missing request/role/DAG inputs, and runtime/effect
incompatibility. Domain choreography remains in the task-local DAG and domain
procedure owner.

## Stop lines

- C2 remains model-neutral.
- The model slug is not copied into role or plan truth.
- A schema-valid binding is not activation, execution, persistence, proof,
  acceptance, landing, or net benefit.
- Historical v1 compatibility is not admission for a new external actor that
  requires the evidence-complete v2 chain.
- Parent/child words in a task request remain first-route compatibility terms,
  not permanent A2A social ontology.
- External effects require matching plan steps and explicit approval bindings;
  the initial Luna admission keeps them disabled.
- Runtime usage is counted, not used as a predeclared execution ceiling. Token,
  wall-time, turn, output, and command observations cannot silently stop an
  incarnation; provider limits and explicit operator interruption remain
  runtime evidence rather than SDK-authored budgets.
