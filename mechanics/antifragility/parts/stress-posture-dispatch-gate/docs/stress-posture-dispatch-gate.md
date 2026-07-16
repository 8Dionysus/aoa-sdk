# Stress Posture Dispatch Gate

## Goal

Teach `aoa-sdk` to treat stress posture as a first-class control-plane input.

The SDK should become better at narrowing, disclosing, and guarding when the
system is under stress.
It should not become a hidden repair daemon.

## Why the SDK is the right stress-posture dispatch gate

The SDK already owns:

- typed loading of source-owned surfaces
- compatibility checks
- typed A2A task-dispatch constraints
- reviewed closeout helpers
- stable workspace reports under `.aoa/`

That makes it the right place to carry stress context across phases into a
visible dispatch decision.

## Stress-aware dispatch posture

Stress signals may come from:

- source-owned receipts
- routing stress hints
- explicit memo failure lessons
- runtime degradation receipts
- compatibility checks tied to the same working surface

The SDK should use these explicit signals to:

- disclose active stress posture at ingress
- narrow task dispatch and blocked actions
- require supervised execution or review when appropriate
- prefer verify and closeout paths before mutation when appropriate
- persist stable stress-aware reports if they fit the existing report surfaces cleanly

## Narrowing rule

Stress posture may only narrow or block behavior.

It may:

- require human review
- push the session toward regrounding
- keep mutation in a visible confirmation lane
- attach evidence refs to a closeout request

It may not:

- silently widen permissions
- auto-repair a runtime
- select, activate, execute, or mutate skills
- claim that a runtime enforced the returned blocked actions

## Phase guidance

### Ingress

Detect stress context and disclose it in the stable ingress report if appropriate.

### Pre-mutation

Respect explicit stress signals derived from owner receipts and routing hints.
If posture is `human_review_first` or `stop_before_mutation`, return the
corresponding blocked actions and let the caller or runtime enforce them.

### Verify

Prefer proof surfaces, current owner artifacts, and bounded eval bundles.

### Closeout

Bundle stress evidence into a reviewed closeout path without forcing immediate promotion to memo, stats, or routing.

## Suggested stable outputs

Possible additive report enrichments:

- stress-posture summary in ingress reports
- stress-aware blocked actions in task-dispatch reports
- reviewed stress bundles in closeout manifests

These should remain subordinate to source-owned meaning.

## Skill boundary

Stress posture is not a skill-retrieval signal. The SDK does not rank skills,
compose a task-local skill DAG, or activate a bundle. Exact bundle inspection
stays on `sdk.skills`; semantic retrieval and composition route to KAG; runtime
execution stays with the host.
