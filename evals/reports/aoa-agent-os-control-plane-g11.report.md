---
schema_version: local_eval_report_note_v1
owner_repo: aoa-sdk
status: draft
authority_boundary: owner-local evidence report only; no verdict, scoring, regression, or proof doctrine authority
---

# Agent OS control-plane G11 local report

## Bounded question

Can a fresh consumer use the installed `aoa-sdk` control plane without an
`aoa-routing` checkout, and do the declared golden and adversarial Agent OS
cases reach their correct typed terminal boundary without hidden activation,
authority drift, or inherited parent context?

This report answers only for the pinned local trial set. It does not issue a
central `aoa-evals` verdict.

## Evidence identity

- SDK source: `6f61aa9682662a919d778bf50c8c22ee9ba0eef1`
- runtime-owner source: `dd4fc056a9ea490df7ca2cc85fe205d4fc38f743`
- installed wheel SHA-256:
  `1ed2330b49e3cfb7307a4e4279eac5c4a0163648faba76259f48b4fab61b830f`
- fresh compiler-v3 chain:
  `fresh-context-compiler-v3-black-box-v1.json`
- isolated lifecycle:
  `isolated-runtime-lifecycle-v1.json`
- adversarial corpus:
  `agent-os-g11-adversarial-corpus-v1.json`

All three child subjects used `fork_turns=none`, exact
`summon-request-v3` passports, named outputs, allowed effects, and stop lines.
Every child return was independently validated and closed through a typed
`summon-result-v3`.

## Observed outcome

- installed-wheel public route, explanation, owner binding, and compiler-v3
  plan construction reproduced eight times in one fresh context;
- the clean federation contained the six required owner repositories and no
  `aoa-routing` checkout;
- the isolated non-executing Runner lifecycle closed after sequential
  approvals, duplicate commands, pause/resume, disconnect, interruption,
  bounded recovery, 64 progress events, and exact `SessionHandle` restore;
- the SDK-local suite completed 16/16 with no skips;
- the runtime-owner A2A/approval suite completed 5/5 with no skips;
- the malformed passport failed on the exact seven absent request fields and
  produced a valid `not_run` result with no child launch or effects.

The first isolated-runtime smoke exposed a real multi-approval reconciliation
defect. Commit `f357e8f7c91850c38e18be7a2490b8e081130b1d`
corrected the pending-set invariant and added a regression case before the
accepted fresh-context run.

## G11 coverage map

| Declared case | Rightful terminal type | Deterministic evidence |
|---|---|---|
| ambiguous intent | blocked `RouteDecision` plus explanation | `sdk:ambiguous-intent` |
| missing capability | blocked `RouteDecision` plus reason code | `sdk:missing-capability` |
| conflicting routes | blocked `RouteDecision`; no lexical fallback | `sdk:conflicting-routes` |
| forbidden action | blocked route/effect posture | `sdk:forbidden-action` |
| approval bypass | rejected runtime command before resume | runtime-owner weakened/bypass tests |
| stale artifact | `AoARunnerError` before dispatch, verified state retained | SDK stale snapshot/observation tests |
| wrong runtime profile | validation error before plan/dispatch | SDK approval-owner and ID-collision tests |
| incomplete passport | valid `summon-result-v3`, `not_run` | seven-field schema adversary |
| incorrect return | typed failed `RunOutcome` or pre-dispatch bridge error | runtime-owner incomplete/conflict tests |
| lost event | `AoARunnerError`, last verified ledger retained | SDK missing/reordered/invalid event tests |
| duplicate execution | same typed status, no new event/effect | SDK duplicate execution test |
| runtime failure | typed recoverable failure, restore, outcome, closeout | SDK disconnect plus isolated runtime receipt |
| inherited-context leakage | accepted fork-without-history returns | three `fork_turns=none` subjects |

The three golden cases cover public route-bind-compile, Runner lifecycle
closeout, and A2A C5 evidence-chain closeout. “Complete evidence chain” means
complete to the rightful stop boundary: a blocked route has no fabricated
`RunPlan` or runtime outcome.

## Authority posture

The SDK resolved and compiled; the reference adapter only witnessed lifecycle
state and explicitly executed no plan steps; `abyss-stack` retained runtime
bridge behavior; `aoa-evals` refs remained external verdict-owner references;
memo/checkpoint and closeout refs stayed owner-qualified. Runtime success was
not converted into an eval verdict.

## Central eval route

Catalog selection found `aoa-bounded-change-quality` as the nearest composite
surface and `aoa-verification-honesty` as its nearest diagnostic neighbor.
They are useful for later workflow review but do not cover typed Agent OS
chain identity, clean-federation independence, isolated recovery, or A2A
return integrity. No central bundle was executed and no central verdict is
claimed.

## Proof ceiling

The retained evidence supports bounded T1/G11 usability and fail-closed
behavior for the pinned cases. It does not prove general agent quality,
production model/tool execution, task effectiveness, cost reduction,
consumer-zero, archive readiness, or stability after future source changes.
Those claims require their own stages and fresh evidence.
