# Compose Closeout After an Immutable Runtime Outcome

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0083
- Original date: 2026-07-26
- Surface classes: public API, model contract, lifecycle, evidence chain, recovery
- SDK facets: control-plane, public interface, runtime entry
- Mechanic parents: boundary-bridge
- Guard families: owner provenance, immutable outcome, partial closeout, exact recovery
- Posture: accepted

## Context

C4 proves that `abyss-stack` can emit a durable runtime-owned outcome before
any central eval, memo retention, reviewed checkpoint closeout, or final
closeout-owner adoption occurs. The C1 model included eval and memory fields
inside `RunOutcome`, and the C3 closeout validator read those fields. A
production runtime cannot fill them honestly: doing so would either synthesize
stronger-owner truth or require mutating a terminal outcome after runtime
completion.

The chain must also be recoverable by stable session or closeout identity
without searching repositories heuristically or copying canonical proof and
memory payloads into the SDK.

## Options Considered

- Mutate `RunOutcome` after eval and retention complete.
- Let the runtime bridge create eval and memory projections.
- Store only loose refs in the final closeout bundle and recover the earlier
  route through workspace search.
- Add a separate owner-safe evidence-chain projection after the immutable
  runtime outcome.

## Decision

Add `aoa_evidence_chain_v1` as a separate SDK projection. It embeds the exact
SDK control-plane objects from intent through runtime outcome and carries only
owner-qualified refs for external eval verdicts, memory receipts, reviewed
checkpoint receipts, and the final closeout bundle.

The new composition route rejects a runtime outcome containing eval, memory,
or closeout refs. Those legacy fields remain in the public v1 model for the
compatibility window, but they are not admitted by the C5 route.

The chain has two explicit dispositions:

- `partial` names every required ref still missing and cannot close runtime
  lifecycle;
- `complete` has all required owner refs and one final closeout bundle.

Required closeout artifact kinds are checked against satisfied plan evidence,
not only against a closeout requirement ID. Checkpoint coverage must bind
required steps and any observed pause or recoverable-failure state.

`EvidenceChainRepository` persists content-addressed immutable revisions under
an explicit absolute root and maintains an atomic exact index. A partial chain
may advance monotonically to complete; complete chains are immutable. Exact
lookup by `SessionHandle` or closeout receipt ID reconstructs the full chain
without owner-path discovery.

`AoARunner.closeout()` accepts the new complete chain while retaining the
existing `CloseoutBundleRef` form during the compatibility window. The Runner
validates cross-owner completeness. Runtime adapters receive only the exact
final bundle and validate runtime scope; they do not interpret external
owner artifacts.

## Owner Boundary

- `aoa-evals` source bundles and admitted evidence own verdict meaning.
- `aoa-memo` owns reviewed retention and memory receipt meaning.
- checkpoint owners own review and checkpoint acceptance.
- the closeout owner named by the plan owns the final bundle.
- runtime owners own events, execution evidence, and `RunOutcome`.
- `aoa-sdk` owns only typed linkage, completeness checks, monotonic projection,
  exact indexing, and Runner admission.

The bounded `aoa-trace-outcome-separation` source contract is the strongest
currently selected central eval fit for the first outcome/path distinction
trial. That selection is navigation only and is not an eval result.

## Consequences

- Positive: runtime outcome identity remains stable across later proof and
  retention work.
- Positive: partial closeout is explicit and inspectable.
- Positive: recovery can start from either stable session or final receipt
  identity.
- Positive: external owner payloads are not copied into the SDK repository.
- Tradeoff: the compatibility window temporarily supports legacy bundle-only
  and C5 chain closeout forms.
- Tradeoff: complete production closeout still requires actual owner artifacts;
  reference fixtures cannot prove those owners acted.

## Source Surfaces

- `src/aoa_sdk/contracts/evidence_chain.py`
- `src/aoa_sdk/control_plane/evidence_chain.py`
- `src/aoa_sdk/control_plane/runner/`
- `src/aoa_sdk/contracts/control_plane.py`
- `mechanics/boundary-bridge/parts/evidence-closeout-chain/`
- `repo:aoa-evals/evals/workflow/aoa-trace-outcome-separation/`
- `skill:aoa-checkpoint-closeout-bridge`

## Follow-Up Route

Bind the first real C4 runtime result to owner-produced eval, memo/checkpoint,
and closeout refs. Then prove the other two golden scenarios and adversarial
partial/recovery paths in the agent-in-the-loop phase. Do not promote a
checkpoint hint or eval selection into an owner verdict.

## Verification

Run the C5 focused suite, C3 regression suite, static checks, topology and
source-home validators, installed-wheel proof, and one cross-owner golden
cycle before convergence landing.
