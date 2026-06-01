# Public Interface

`sdk/public-interface/` owns SDK-facing route posture for consumer entrypoints.

It does not implement those entrypoints. Implementation stays in
`src/aoa_sdk/`; this branch names the public contract contour and points to
the proof route.

## Families

| Family | Role | Next route |
| --- | --- | --- |
| `python-api/` | importable Python API posture | `src/aoa_sdk/api.py`, `src/aoa_sdk/__init__.py` |
| `cli-contract/` | CLI control-plane posture | `src/aoa_sdk/cli/` |
| `model-contract/` | typed model and truth-label posture | `src/aoa_sdk/models.py`, `schemas/` |

## Stop Lines

- Do not add implementation code here.
- Do not treat docs posture as stronger than tests.
- Do not widen public promises without validation.
