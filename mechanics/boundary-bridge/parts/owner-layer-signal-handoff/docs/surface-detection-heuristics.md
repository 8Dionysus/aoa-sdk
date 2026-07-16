# AoA Surface Detection Heuristics

The deterministic rules live in `src/aoa_sdk/surfaces/`. They identify a
possible owner lane; they do not perform semantic retrieval or execution.

| Signal | Trigger family | Owner | State | Existing surface |
| --- | --- | --- | --- | --- |
| `proof-need` | verify, proof, regression, contract | `aoa-evals` | `candidate-now` | `aoa-evals.runtime_candidate_template_index.min` |
| `recall-need` | recall, memory, provenance, history | `aoa-memo` | `candidate-now` | `aoa-memo.memory_catalog.min` |
| `scenario-recurring` | recurring workflow, sequence, checkpoint | `aoa-playbooks` | `candidate-later` | `aoa-playbooks.playbook_registry.min` |
| `role-posture` | agent, role, handoff, orchestrator | `aoa-agents` | `candidate-now` | `aoa-agents.runtime_seam_bindings` |
| `repeated-pattern` | repeat, again, recurring pattern | `aoa-techniques` | `candidate-later` | `aoa-techniques.technique_promotion_readiness.min` |

Direct layer words may also emit exact owner-lane candidates. `skill` maps to
the `aoa-skills` catalog; it never maps to an installed bundle or generic
routing result.

`repeated-pattern` is restricted to `closeout` or `checkpoint`. No host skill
session or activation signal widens that threshold.

Every emitted execution hint remains non-executable. Deep skill or capability
retrieval belongs to KAG and the executing agent; runtime selection belongs to
the host.
