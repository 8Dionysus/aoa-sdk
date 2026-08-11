# Validation Evidence Graph

This part owns the SDK-local transformation from release claims to explicit,
dependency-aware validation evidence and a bounded sufficiency receipt.

## Role

Input: an owner-authored claim/evidence manifest, one full or bounded claim
profile, an optional shadow changed-path set, and the invoking environment.

Output: direct-argv validation execution plus one identity-bound receipt that
names required, satisfied, and missing evidence. The default full profile
preserves the complete `scripts/release_check.py` battery while scheduling
independent work concurrently.

Owner: `aoa-sdk` owns only its local claim set, manifest, scheduler, and
sufficiency decision. `aoa-evals` owns central proof doctrine and verdicts;
sibling repositories own their own claims and validators; GitHub is only an
execution adapter.

## Active surfaces

- [Claim/evidence manifest](config/validation_graph.json)
- [Bounded graph runner](scripts/validation_graph.py)
- [Contract and scheduler regressions](tests/test_validation_graph.py)
- [Validation route](VALIDATION.md)
- `evals/suites/aoa-validation-evidence-graph.suite.md`

## Current posture

The full profile is eligible for owner-gate trials only when every declared
node passes. Path routing remains `shadow_only` and can never authorize the
owner gate. Cross-run receipt reuse is intentionally absent until exact input,
environment, freshness, and tamper rules have their own accepted cases.

## Next route

Compare serial, bounded DAG, worker, static shard, routing, and reuse methods
under the local eval design. Route any portable eval or central verdict to
`aoa-evals`, measurement grammar to `aoa-stats`, host resource admission to
`abyss-machine`, and any sibling adoption back to that repository's owner.
