# Validation Evidence Graph Contract

## Allowed outputs

- An owner-local claim, risk, and required-evidence manifest.
- A deterministic activated dependency subgraph.
- Direct-argv bounded process execution.
- Ordered node and step results with digests and bounded output tails.
- A full or explicitly bounded owner-local sufficiency decision.
- Non-authoritative shadow routing comparisons.

## Required guards

- Full fallback for unknown changed paths.
- Unique claim, route, node, step, and evidence-provider identities.
- Acyclic dependencies and explicit timeouts.
- Every full-profile claim and required evidence remains declared.
- Failed, timed-out, blocked, stale, missing, or ambiguous evidence cannot be
  sufficient.
- Partial and shadow receipts cannot authorize the full owner gate.
- Receipt identity binds source state, manifest, commands, environment,
  evidence, and outcomes.

## Stop-lines

- Do not treat scheduling as proof weakening or delete a slow obligation.
- Do not let CI configuration own claim meaning.
- Do not infer sibling sufficiency from SDK evidence.
- Do not turn a local receipt into an `aoa-evals` verdict.
- Do not enable path routing or receipt reuse as a landing authority before
  no-miss, tamper, freshness, and hosted comparisons are accepted.
- Do not conceal shell execution, hidden network effects, or mutable sibling
  operations inside a graph node.

## Owner split

`aoa-sdk` owns this reference implementation and only its own release claims.
Each AbyssOS repository must author its own claims, risks, evidence providers,
and sufficiency rule. `aoa-evals` owns comparative proof adoption,
`aoa-stats` owns shared measurement grammar, `abyss-machine` owns host
admission, and GitHub owns neither source truth nor proof meaning.
