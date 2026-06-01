# A2A Quest Passport Secondary Tier Naming

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0039
- Original date: 2026-06-01
- Surface classes: active naming, typed model, checkpoint, A2A contract
- SDK facets: A2A rebase, child-task reentry, active naming, request payload
- Mechanic parents: checkpoint
- Guard families: active naming, route clarity, part validation
- Posture: accepted

## Context

`QuestPassport` carried a `fallback_tier` field. The field was SDK-owned A2A
request vocabulary, not a sibling-owned generated schema and not a legacy input
alias.

The current mechanics refactor is removing active fallback vocabulary from SDK
routes. In this passport, the intended meaning is an optional secondary tier for
delegation planning.

## Decision

Rename the field to `secondary_tier`.

Update the child-task reentry fixture and SDK API regression so emitted summon
request payloads use `secondary_tier` and do not emit `fallback_tier`.

## Rationale

`secondary_tier` names the route role directly. It tells an agent that this is
another planned tier, not a hidden fallback or substitute for the primary
delegate tier.

## Consequences

- `src/aoa_sdk/a2a/rebase/models.py` uses `secondary_tier`.
- The generated A2A summon/return checkpoint fixture emits `secondary_tier`.
- Child-task reentry tests prove `fallback_tier` is not emitted in the SDK
  request payload.

## Source Surfaces

- `src/aoa_sdk/a2a/rebase/models.py`
- `mechanics/checkpoint/parts/child-task-reentry/`

## Follow-Up Route

If older external A2A payloads appear with `fallback_tier`, route that as an
explicit compatibility input decision instead of reintroducing the old name as
active SDK output.

## Verification

```bash
python -m pytest -q mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_sdk_api.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_e2e_fixture.py
python -m ruff check src/aoa_sdk/a2a/rebase/models.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_sdk_api.py
```
