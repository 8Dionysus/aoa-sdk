# Hook Pack Producer Guide

This guide documents the four producer families seeded in the hook pack.

## `jsonl_receipt_watch`

Use for owner-local receipt streams such as `.aoa/live_receipts/*.jsonl`.

Expected contract:

- each line is one JSON object
- `signal_rules` describe which observations to emit
- `record_id_field` chooses the suffix used in `evidence_refs`

Good for:

- receipt publication
- candidate-harvest hints
- second-consumer hints
- route receipts that should stay reviewable

## `skill_trigger_gap_watch`

Use for `aoa-skills` description-trigger suites plus one or more recent skill-evidence surfaces.

This producer compares:

- trigger cases
- recent skill receipts or session-growth artifacts

It emits bounded gaps such as:

- `should_trigger_missing`
- `prefer_other_skill_gap`
- `manual_invocation_boundary_seen`

This is a gap detector, not an activation engine.

## `harvest_pattern_watch`

Use for harvest JSON, harvest JSONL, real-run Markdown, and gate-review Markdown.

It supports:

- file-level phrase matching for Markdown
- field-level signal rules for JSON and JSONL

Good for:

- repeated scenario shape
- bounded parallel split
- reviewable split repetition
- automation readiness pressure

## `runtime_candidate_watch`

Use for selected runtime evidence packets that may begin hardening into portable proof surfaces.

It can emit:

- `trace_bridge_receipt_ready`
- `runtime_candidate_selected`
- `portable_claim_repeat`
- `overclaim_detected`

It never turns runtime artifacts into proof canon by itself.

## Missing-path posture

A missing source file should stay visible in the hook run report.
That visibility is part of the point. The hook pack is also a connectivity probe.
