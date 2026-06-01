# Model Contract

Role: route typed model and truth-label posture.

Input: Pydantic model fields, public schema posture, validation aliases, truth
labels, and emitted field names.

Output: implementation route, schema route, compatibility route, or decision
record.

Owner: `sdk/public-interface/AGENTS.md` and
`sdk/source_home.manifest.json#model_contract`.

Next route: `src/aoa_sdk/models.py`, `schemas/`,
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`, and model
tests.

Stop line: compatibility input aliases may stay readable, but stale alias
vocabulary should not become active SDK output names.
