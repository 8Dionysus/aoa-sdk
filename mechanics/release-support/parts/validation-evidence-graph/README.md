# Validation Evidence Graph

This part owns the SDK-local transformation from release claims to explicit,
dependency-aware validation evidence and a bounded sufficiency receipt.

## Role

Input: an owner-authored claim/evidence manifest, one full or bounded claim
profile, an optional shadow changed-path set, and the invoking environment.
An external owner manifest also carries an exact `aoa_validation_runner_pin_v1`
for the SDK runner source.

Output: direct-argv validation execution plus one identity-bound receipt that
names required, satisfied, and missing evidence. The default full profile
preserves the complete `scripts/release_check.py` battery while scheduling
independent work concurrently.

Owner: `aoa-sdk` owns its local claim set and the reference scheduler ABI.
Sibling repositories may invoke that scheduler with an explicit owner
`--repo-root`, but they still own their manifests, claims, validators, and
sufficiency decisions. `aoa-evals` owns central proof doctrine and verdicts;
GitHub is only an execution adapter.

## Active surfaces

- [Claim/evidence manifest](config/validation_graph.json)
- [Bounded graph runner](scripts/validation_graph.py)
- [Contract and scheduler regressions](tests/test_validation_graph.py)
- [Validation route](VALIDATION.md)
- `evals/suites/aoa-validation-evidence-graph.suite.md`

## Current posture

The reviewed three-worker full profile is the default implementation behind
`scripts/release_check.py` and `Repo Validation`. Every declared node must pass
and the retained serial command inventory remains the exact completeness
oracle and rollback. Path routing remains `shadow_only` and can never authorize
the owner gate. Cross-run receipt reuse is intentionally absent until exact
input, environment, freshness, and tamper rules have their own accepted cases.
The runner binds its own source-checkout commit, tree, worktree state, and file
digest separately from the owner repository. External runs additionally bind
the exact runner pin declared by the owner manifest. The receipt records a
secret-safe digest of the complete inherited environment before and after
execution and the declared runner pin; unavailable or changing
runner/environment identity makes a receipt insufficient.

## Next route

Continue comparing the promoted graph with the serial oracle and evaluate
routing and reuse methods under the local eval design. Sibling pilots should
reuse only the scheduler ABI, pass their repository root explicitly, and keep
their complete serial oracle until owner-local admission. Route any portable
eval or central verdict to `aoa-evals`, measurement grammar to `aoa-stats`,
host resource admission to `abyss-machine`, and every sibling adoption back to
that repository's owner.
