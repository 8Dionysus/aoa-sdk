---
schema_version: local_eval_suite_note_v1
owner_repo: aoa-sdk
status: draft
authority_boundary: owner-local evidence support only; no verdict, scoring, regression, or proof doctrine authority
---

# Agent OS control-plane G11 suite

## Invariant

Given an owner-pinned route snapshot, typed intent, scenario binding, runtime
profile, and public lifecycle client, the SDK must either produce one
deterministic owner-qualified chain or stop with a typed fail-closed result. It
must not guess a route, weaken approval, replay an effect, accept stale
evidence, or repair a broken event chain heuristically.

## Manual evidence roots

- the installed-wheel golden chain establishes the positive public
  `resolve -> explain -> bind -> compile` contour;
- the fresh-context black-box receipt checks whether a consumer can discover
  and use that contour without parent-session history;
- the selected source tests preserve the exact negative, collision, recovery,
  and regression examples that shaped the automated cases.

Agent traces remain observations. The deterministic cases are the local
mechanical checks. Neither layer is a central `aoa-evals` verdict.

## Case families

Positive cases reproduce compilation and normal lifecycle completion.
Negative cases cover absent capability, ambiguous and conflicting route
selection, forbidden effects, stale snapshots and observations, missing or
reordered event slices, invalid runtime events, and disconnect recovery.
Collision cases cover runtime approval identity and duplicate command
idempotency. Regression cases keep the owner-pinned public golden chain and
fresh-context receipt separately visible.

The wrapper runs exact pytest node IDs in isolated child pytest processes. A
case is accepted only when the child exits zero and the wrapper retains its
stdout/stderr on failure. An unknown or renamed node is therefore a hard
failure instead of an implicit skip.

## Runner contract

- input: the tracked SDK test sources and this wrapper;
- output: one pytest result per exact case plus a terminal wrapper exit code;
- accepted outcome: every selected child node exits `0`;
- timeout: 900 seconds for the wrapper, with 120 seconds per child node;
- cleanup: pytest cache is disabled and the wrapper creates no repository
  artifacts;
- actual effect: local subprocess execution and ephemeral interpreter state;
- false-green guard: exact node IDs, per-node subprocess boundaries, no
  `xfail`, no skip acceptance, and owner-port hash revalidation immediately
  before execution.

The sidecar's `ready` state proves only the reviewed source contract. It does
not prove a pinned interpreter, dependency environment, runtime
reproducibility, fresh-context behavior, cross-repository runtime behavior, or
G11 completion.

## Rejected central surfaces

`aoa-bounded-change-quality` is the nearest composite workflow eval and
`aoa-verification-honesty` is its nearest diagnostic neighbor. Both remain
useful review layers, but neither covers typed Agent OS chain identity,
clean-federation independence, isolated runtime recovery, or summon-return
integrity. Portable adoption or a central verdict therefore routes to
`aoa-evals` after owner review of this local evidence.
