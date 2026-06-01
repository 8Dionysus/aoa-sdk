# Recurrence Review Decision Closure

This seed closes the loop after `review_queue`, `candidate_dossier_packet`, and `owner_review_summary`.

## Core rule

A review decision is an owner-authored closure packet. It may close, defer, reanchor, split, merge, reject, or suppress a recurrence beacon. It must not promote canon, accept a skill, approve an eval, widen a playbook, or mint owner objects from `aoa-sdk`.

The SDK may prepare a decision template and carry provisional lineage. The owner repo must own the actual decision surface and any owner-assigned identifiers.

## Decision actions

- `accept`: owner accepts the pressure and records followthrough surfaces.
- `reject`: owner rejects the pressure with rationale.
- `defer`: owner keeps the signal open until more evidence appears.
- `reanchor`: owner points the signal to a better owner surface.
- `split`: owner splits one noisy pressure into bounded smaller pressures.
- `merge`: owner absorbs the pressure into an existing surface.
- `suppress`: owner records a narrow false-positive or intentional-restraint memory.

## Outputs

- `owner_review_decision` records one owner decision over one or more beacon refs.
- `review_decision_ledger` summarizes accepted/rejected/deferred/suppressed decisions.
- `review_suppression_memory` preserves narrow future quieting rules.
- `review_decision_close_report` joins decisions back to the queue and leaves unresolved items visible.

## Boundary

This layer is a closure ledger, not a verdict authority. It exists so recurrence can remember what a human or owner-layer review decided without turning the beacon layer into governance.
