# Recurrence Beacon Layer

This note defines the second programmable contour of recurrence.

The first contour already exists:

- detect change
- expand the impacted graph
- plan owner-boundary follow-through
- surface connectivity gaps
- preserve reviewed return handoffs

That contour answers an obligation question:

> what now needs to be refreshed, checked, rebuilt, rerouted, or handed back?

The beacon layer adds a different question:

> what pattern is trying to emerge here, and which owning repo should review it?

## Core split

Keep these lanes separate.

- `obligation recurrence`
  - owned by `detect`, `plan`, `doctor`, and `return-handoff`
  - produces required follow-through
- `emergence recurrence`
  - owned by `observe`, `beacon`, `ledger`, and `usage-gaps`
  - produces advisory candidate pressure

Do not collapse them into one planner.

## Packet family

The beacon layer uses four packet shapes.

- `ObservationPacket`
  - raw or normalized evidence signals
  - may come from change detection, receipts, closeout notes, trigger evals, review notes, runtime artifacts, or harvest notes
- `BeaconPacket`
  - typed candidate pressure
  - status ladder: `hint -> watch -> candidate -> review_ready`
- `CandidateLedger`
  - durable list of candidate pressure records
  - suitable for witness-style note taking and later review
- `UsageGapReport`
  - narrow report for missing or drifting skills

## Status ladder

The ladder is deliberately soft.

- `hint`
  - something worth keeping in view
- `watch`
  - repeated or stronger pressure, but still not enough to treat as a candidate
- `candidate`
  - strong enough to open a bounded review surface
- `review_ready`
  - enough evidence to prepare a review packet, not to auto-promote

A beacon is not a verdict.

## Suppression

A real pattern may still need to stay lower on the ladder.

Examples:

- a technique candidate overlaps an already landed bundle
- a playbook-like shape is still too workflow-local
- an eval signal is starting to overclaim beyond bounded evidence
- a subagent split is useful but still drifting toward hidden orchestration

This is why beacon rules support `suppress_when`.

Suppression may cap the status at `watch`, but it should not erase the signal. Suppressed pressure is often exactly the thing that later becomes reviewable once one missing boundary sharpens.

## Decision ownership

Beacon output never changes repo truth by itself.

- `aoa-techniques` still owns technique distillation and canonical review
- `aoa-skills` still owns bounded skill bundles and trigger surfaces
- `aoa-evals` still owns claim wording and verdict posture
- `aoa-playbooks` still owns scenario composition and composition gates

The beacon layer is there to say "pressure is here", not "the decision has already happened".
