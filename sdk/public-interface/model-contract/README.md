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

The R2 Agent OS models are authored in
`src/aoa_sdk/contracts/control_plane.py` and compatibility-reexported through
`aoa_sdk.models`. They are strict owner-qualified references and
runtime-neutral lifecycle contracts. Their presence does not make sibling
objects SDK source truth or activate a runner. C1 now emits the existing
`RouteDecision` and `RouteExplanation` contracts from a versioned
deterministic resolver; it does not widen the model family or make a selected
candidate executable.

The organ-access model family is authored in
`src/aoa_sdk/contracts/organs.py`, published as deterministic JSON Schema in
`schemas/organ-access/`, and re-exported through `aoa_sdk.models`. It keeps
owner payloads generic and typed while strictly normalizing access metadata,
effects, policy, credential classes, revisions, freshness, compatibility, and
the independent maturity axes. These models authorize neither runtime
execution nor owner-truth acceptance.
