# Agent Incarnation Binding Contract

## SDK owns

- byte-compatible `aoa_agent_incarnation_binding_v1` historical-read shape;
- required `aoa_agent_incarnation_binding_v2` obligation, mandate,
  role-resolution, fit-query-result, fit-projection, realization, runtime, and
  exact content-addressed runtime-subject canonical-digest chain for new
  external actors;
- exact cross-object validation against one `RunPlan`;
- optional exact `aoa-session-memory` continuity-capsule reference carry from
  plan through binding and continuation without reading or copying its content;
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
- `aoa-session-memory` owns continuity-capsule content, portable/private view
  meaning, omissions, protected-tail posture, and compaction evidence;
- the target owner and human approval route own acceptance and effects.

## Admission order

```text
RunPlan
  + exact task request
  + exact role contract
  + exact model realization
  + exact content-addressed runtime subject
  + exact runtime/tool profile
  + exact workspace source
  + bounded permission plus observe-only metering, stop and wake policies
  -> AgentIncarnationBindingV2 for a new external actor
  -> AgentIncarnationBinding only when reading historical v1 evidence
  -> runtime-owner delivery binding
```

The SDK binds refs; it does not select the model, launch a process, infer a
model-fit claim, or grant an effect.

## Delegation classes and current adapter admission

The shared `parent_holder_ref` is an owner-qualified `ContentRef` to the
existing parent holder or task context. It does not require a permanent Goal
object. A formal external actor still needs its complete obligation, mandate,
role, incarnation, responsibility-transfer, continuation, runtime, and return
chain from the named owners.

Choose the class from its required properties before naming an adapter. The
current SDK source admits this matrix:

| Class | Required properties | Adapter admission in `aoa_sdk` |
| --- | --- | --- |
| `ephemeral_read_worker_v1` | Bounded immutable inputs; stateless, read-only work; content-addressed `abyss-stack` result and economy observation; parent retains responsibility; no role formation or durable transfer | `local_provider` only. `codex_cli` and built-in Codex subagents are rejected. |
| `external_incarnation_v1` | Transferred responsibility; exact `aoa-agents` role and mandate; `aoa-models` realization; SDK incarnation and continuation refs; `abyss-stack` process, session, and event refs; required `aoa-agents` transfer and reviewed-return refs; separately owned lifecycle refs | `codex_cli` or `local_provider`. The SDK records the kind and owner-qualified implementation ref; it does not prove that a runtime implementation is available or admitted. |

For `external_incarnation_v1`, `eval_ref`, `closeout_ref`, and
`acceptance_ref` are optional lifecycle evidence at this boundary. When
present, each keeps its exact owner/schema contract and all supplied lifecycle
refs remain distinct. The required `reviewed_return_ref` is a separate
`aoa-agents` return disposition; runtime completion or a transport receipt does
not supply it automatically.

The concrete `abyss-stack` adapter profiles are default-off and set
`uses_builtin_codex_subagents` to `false`; activation remains an explicit
runtime-owner decision. The SDK class ABI has no launch or activation side
effect. Ordinary native Codex helpers use their existing task context and stay
outside these formal AoA classes; their execution does not create an
`EphemeralReadWorkerV1` or `ExternalIncarnationV1` admission.

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
- A capsule reference is not capsule admission, freshness, materialization, or
  proof that a compaction boundary occurred.
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
