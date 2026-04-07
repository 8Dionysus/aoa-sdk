# AoA Surface Detection Heuristics

Wave one keeps heuristics in Python code under `src/aoa_sdk/surfaces/`.
Example JSON belongs in docs or tests only; runtime does not depend on packaged
seed data.

## Deterministic rules

| Signal | Trigger family | Owner repo | Object kind | State | Execution lane | Existing surface |
| --- | --- | --- | --- | --- | --- | --- |
| `proof-need` | verify, proof, regression, contract, invariant | `aoa-evals` | `eval` | `candidate-now` | `inspect-expand-use` | `aoa-evals.runtime_candidate_template_index.min` |
| `recall-need` | recall, memory, provenance, prior, history | `aoa-memo` | `memo` | `candidate-now` | `inspect-expand-use` | `aoa-memo.memory_catalog.min` |
| `scenario-recurring` | recurring, runbook, workflow, sequence, checkpoint | `aoa-playbooks` | `playbook` | `candidate-later` | `closeout-harvest` | `aoa-playbooks.playbook_registry.min` |
| `role-posture` | agent, role, handoff, orchestrator, persona | `aoa-agents` | `agent` | `candidate-now` | `inspect-expand-use` | `aoa-agents.runtime_seam_bindings` |
| `repeated-pattern` | repeat, repeated, again, pattern, recurring | `aoa-techniques` | `technique` | `candidate-later` | `closeout-harvest` | `aoa-techniques.technique_promotion_readiness.min` |

## Explicit layer requests

When intent text directly names an AoA layer, wave one can surface a
`candidate-now` owner-layer note without pretending it is already activated.

- `skill` -> `aoa-skills:layer-request`
- `eval` -> `aoa-evals.runtime_candidate_template_index.min`
- `memo` or `memory` -> `aoa-memo.memory_catalog.min`
- `playbook` -> `aoa-playbooks.playbook_registry.min`
- `agent` -> `aoa-agents.runtime_seam_bindings`
- `technique` -> `aoa-techniques.technique_promotion_readiness.min`

## Repeated-pattern threshold

`repeated-pattern` only fires when the intent includes repeat-pattern language
and one of these is true:

- the current phase is `closeout`
- the runtime session already has active skills

This keeps technique hints from appearing on one-off ingress passes that only
mention a pattern once.

## Skill-item mapping

- `activate_now` from the skill prelude becomes `state=activated` and
  `lane=skill-dispatch`
- router-only `must_confirm` or router-only `suggest_next` items with
  `manual_fallback_allowed=true` become `state=manual-equivalent` and
  `lane=manual-fallback`
- skill suggestions without an honest manual-equivalent posture stay in the
  skill report and do not get duplicated into surface items

## Guardrails

- non-skill items never enter `immediate_skill_dispatch`
- heuristics propose owner-layer inspection surfaces, not fake repo paths
- source-owned typed surfaces remain the truth if seed wording and live repo
  reality diverge
