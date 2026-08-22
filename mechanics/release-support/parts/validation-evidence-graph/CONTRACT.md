# Validation Evidence Graph Contract

## Allowed outputs

- An owner-local claim, risk, and required-evidence manifest.
- A deterministic activated dependency subgraph.
- Direct-argv bounded process execution.
- Ordered node and step results with digests and bounded output tails.
- A full or explicitly bounded owner-local sufficiency decision.
- Non-authoritative shadow routing comparisons.
- A versioned `aoa_validation_runner_pin_v1` in an owner manifest when the
  reference runner executes outside its SDK source checkout.

## Required guards

- Full fallback for unknown changed paths.
- Unique claim, route, node, step, and evidence-provider identities.
- Acyclic dependencies and explicit timeouts.
- Every full-profile claim and required evidence remains declared.
- Failed, timed-out, blocked, stale, missing, or ambiguous evidence cannot be
  sufficient.
- Partial and shadow receipts cannot authorize the full owner gate.
- Receipt identity binds source state, manifest, commands, environment,
  and clean or dirty identities of nested Git verifier checkouts,
  evidence, and outcomes.
- The receipt binds a secret-safe digest of the complete inherited execution
  environment before and after the run; environment drift is insufficient.
- The receipt records the declared runner pin alongside the observed runner
  identities so an external-owner provenance comparison is self-contained.
- When the reference runner executes for another owner repository, the receipt
  binds the owner repository and runner source checkout as distinct Git
  identities. Missing or changing runner source identity fails closed.
- An external owner run requires a runner pin with the exact SDK runner path,
  source commit, and file digest; missing or mismatched pins are insufficient.
- The explicit owner root must equal that checkout's resolved Git top-level;
  a nested directory cannot borrow its parent repository identity.

## Stop-lines

- Do not treat scheduling as proof weakening or delete a slow obligation.
- Do not let CI configuration own claim meaning.
- Do not infer sibling sufficiency from SDK evidence.
- Do not turn a local receipt into an `aoa-evals` verdict.
- Do not enable path routing or receipt reuse as a landing authority before
  no-miss, tamper, freshness, and hosted comparisons are accepted.
- Do not conceal shell execution, hidden network effects, or mutable sibling
  operations inside a graph node.
- Do not serialize inherited environment values, including credentials; bind
  them only through the secret-safe environment digest.

## Owner split

`aoa-sdk` owns this reference scheduler implementation and only its own release
claims. Each AbyssOS repository must author its own claims, risks, evidence
providers, sufficiency rule, runner pin, and admission decision. An owner may
leave the pin null only for the SDK-local run where the owner and runner source
checkout are the same; an external owner must supply the exact pin. `aoa-evals`
owns comparative proof adoption,
`aoa-stats` owns shared measurement grammar, `abyss-machine` owns host
admission, and GitHub owns neither source truth nor proof meaning.
