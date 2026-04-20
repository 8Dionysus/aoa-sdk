# Recurrence Rollout Bundle

This note defines a bounded rollout companion for recurrence adoption.

## Core rule

Treat recurrence rollout as a campaign with explicit drift and rollback posture.

## Bundle objects

- `campaign_window`
- `drift_review_window`
- `rollback_followthrough_window`

## Stop lines

Open drift or rollback windows when:

- hook wiring drifts
- review surfaces stop materializing
- doctor reports move into high severity
- proof alarms begin to accumulate

The bundle remains a review surface. It does not become a scheduler or a second playbook.
