# Review Queue Insert

Land this after the hook pack.

## Files added or changed

- `src/aoa_sdk/recurrence/review.py`
- `src/aoa_sdk/recurrence/models.py`
- `src/aoa_sdk/recurrence/api.py`
- `src/aoa_sdk/recurrence/io.py`
- `src/aoa_sdk/recurrence/cli.py`
- schemas and examples for the new review surfaces

## Operational sequence

A thin review flow now becomes:

1. `aoa recur hooks run --event session_stop`
2. `aoa recur observe ...`
3. `aoa recur beacon ...`
4. `aoa recur usage-gaps ...`
5. `aoa recur review-queue ...`
6. `aoa recur review-dossiers ...`
7. `aoa recur review-summary ...`

That sequence still emits candidates for owner review. It does not auto-promote anything.
