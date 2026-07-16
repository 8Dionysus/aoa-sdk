# Recurrence Review Surfaces

This note defines the owner-facing review surfaces that sit above recurrence beacons.

## Core rule

The queue is a review surface, not a verdict surface.

A review queue may say:

- this candidate looks real enough to inspect
- this omission is noisy enough to stop ignoring
- this proof boundary may be stretching too far

It may not say:

- canonical promoted
- skill accepted
- eval approved
- playbook widened

## Families

- `review_queue` keeps a prioritized owner-facing worklist
- `candidate_dossier_packet` turns each queue item into a short review packet
- `owner_review_summary` compresses the queue by owner, lane, status, and kind

## Visibility posture

By default the queue keeps `candidate` and `review_ready` rows, plus watch-level
skill usage gaps only when an owner explicitly authored the evidence-backed
beacon. The SDK does not create those gaps from visibility, selection, loading,
mention, semantic similarity, or missing receipts.
