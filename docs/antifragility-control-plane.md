# Antifragility Control Plane

## Goal

Teach `aoa-sdk` to treat stress posture as a first-class control-plane input.

The SDK should become better at narrowing, disclosing, and guarding when the system is under stress.
It should not become a hidden repair daemon.

## Why the SDK is the right wave-2 seam

The SDK already owns:

- typed loading of source-owned surfaces
- compatibility checks
- phase-aware skill detection and dispatch
- reviewed closeout helpers
- stable workspace reports under `.aoa/`

That makes it the right place to carry stress context across phases.

## Stress-aware dispatch posture

Stress context may come from:

- source-owned receipts
- routing stress hints
- explicit memo failure lessons
- runtime degradation receipts
- compatibility checks tied to the same working surface

The SDK should use this context to:

- disclose active stress posture at ingress
- narrow candidate skills during detection
- block auto-activation when review is required
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
- auto-activate new skills that would otherwise require confirmation

## Phase guidance

### Ingress
Detect stress context and disclose it in the stable ingress report if appropriate.

### Pre-mutation
Respect stress-aware routing hints and owner receipts.
If posture is `human_review_first` or `stop_before_mutation`, keep mutation blocked.

### Verify
Prefer proof surfaces, current owner artifacts, and bounded eval bundles.

### Closeout
Bundle stress evidence into a reviewed closeout path without forcing immediate promotion to memo, stats, or routing.

## Suggested stable outputs

Possible additive report enrichments:

- stress-context summary in ingress reports
- stress-aware guard reasons in pre-mutation guard reports
- reviewed stress bundles in closeout manifests

These should remain subordinate to source-owned meaning.
