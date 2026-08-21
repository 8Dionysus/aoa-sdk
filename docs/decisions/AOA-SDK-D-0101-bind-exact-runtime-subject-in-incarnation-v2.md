# Bind the exact runtime subject in incarnation v2

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0101
- Original date: 2026-08-20
- Surface classes: public API, model contract, runtime boundary, artifact identity
- SDK facets: control-plane, runtime entry, incarnation binding
- Mechanic parents: boundary-bridge, runtime-seam
- Guard families: owner provenance, exact binding, model-fit evidence, artifact trust
- Posture: accepted

## Context

`aoa-models` can now qualify a current realization against an exact
content-addressed runtime package. A v2 incarnation that retained the model
realization and fit projection but omitted that package identity could be
prepared against one Codex package and launched through another while all
existing SDK refs remained structurally valid.

The executable path and reported runtime version are not package identity:
`current` can move and equal version strings can name different bytes or
companion sets.

## Options Considered

- Rely on runtime version and executable path outside the binding.
- Carry the runtime subject only in the outer summon or launch request.
- Make the exact `kind`, `source`, and SHA-256 digest a required field of the
  evidence-complete v2 incarnation binding.

## Decision

Require one strict `IncarnationRuntimeSubject` in every new
`AgentIncarnationBindingV2`. Include it in the canonical binding digest and
require callers to obtain the exact subject through the `aoa-models` fit
query. Preserve v1 unchanged for historical reads.

The SDK binds the owner-supplied identity but does not determine which package
fits, admit artifact bytes, resolve an executable path, or launch a process.

## Rationale

The physical model incarnation is the combination of model realization and
runtime package, not a model slug plus a mutable path. Keeping the exact
subject in the same content-addressed binding closes the prepare-to-launch
identity gap and lets downstream owners reject substitution without copying
model-fit meaning into the SDK.

## Consequences

- New v2 callers must supply exact runtime package identity; stale callers fail
  closed instead of silently falling back to path or version identity.
- Any subject change produces a different binding digest and requires a fresh
  fit query and incarnation binding.
- Historical v1 receipts remain readable and unchanged.
- `aoa-models` still owns fit and subject meaning, artifact-trust controls own
  package admission, and `abyss-stack` still owns path resolution and launch.

## Source Surfaces

- `src/aoa_sdk/contracts/incarnation.py`
- `src/aoa_sdk/control_plane/incarnation.py`
- `mechanics/boundary-bridge/parts/agent-incarnation-binding/schemas/agent-incarnation-binding-v2.schema.json`
- `mechanics/boundary-bridge/parts/agent-incarnation-binding/tests/test_agent_incarnation_binding.py`

## Follow-Up Route

Require the same exact subject in `aoa-agents` route preparation, compare it
with the selected `aoa-models` fit candidate, and preserve it through the
`abyss-stack` runtime launch and terminal evidence chain.

## Verification

Run the v1/v2 schema generator check, part-local tests, lint, mypy, mechanics
topology, source-home validation, decision-index check, and repository release
gate. Pair SDK proof with a real `abyss-stack` launch canary; SDK validation is
not runtime execution proof.
