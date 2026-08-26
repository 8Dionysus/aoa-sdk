# Provider-Neutral Programmatic Execution Contract

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0104
- Original date: 2026-08-26
- Surface classes: public API, runtime boundary, adapter protocol, observation
- SDK facets: control-plane, runtime entry, public interface
- Mechanic parents: runtime-seam
- Guard families: explicit activation, effect ceiling, observation integrity
- Posture: accepted

## Context

Direction 4 needs one ABI that can compare ordinary direct tool calling with a
programmatic execution mode across Codex and a local-model route. The SDK must
describe that boundary without becoming a provider launcher or runtime policy
owner. Runtime execution, sandbox enforcement, and durable evidence belong to
`abyss-stack`.

## Options Considered

- Add provider-specific request fields to the existing Agent OS bridge.
- Keep each provider's tool execution shape separate.
- Add one typed, provider-neutral contract with explicit runtime admission and
  observation missingness, then let the runtime own adapters.

## Decision

Add `aoa_programmatic_tool_execution_v1` under the SDK Runtime Seam. The
contract binds execution and correlation identity, direct/programmatic mode,
stable tool handles, plan and runtime-profile refs, sandbox/effect ceiling,
default-off activation, and required observation dimensions. It carries
observed economy counters, tool-call records, intermediate refs, and typed
failures without introducing token budgets or provider selection.

`abyss-stack` owns the runtime adapter interface and concrete provider
adapters. An observation is admissible only when it repeats the exact request
digest and satisfies the request's handle, ceiling, and missingness rules.

## Rationale

One neutral request and observation shape makes paired direct/programmatic
experiments comparable while leaving Codex host details and local-model
transport details inside their adapters. Explicit not-admitted state prevents
source presence from becoming activation.

## Consequences

- SDK imports remain data-only and independent of live providers.
- Runtime adapters must supply an explicit admission and a complete or
  explicitly unavailable observation.
- Economy values remain measurements, not hidden execution ceilings.
- Runtime/eval/promotion and owner acceptance still require later paired
  baseline evidence.

## Source Surfaces

- `src/aoa_sdk/contracts/programmatic_execution.py`
- `src/aoa_sdk/models.py`
- `mechanics/runtime-seam/parts/programmatic-tool-execution/`
- `mechanics/topology.json`

## Follow-Up Route

Implement and validate the runtime adapters in the
`abyss-stack` governed-execution programmatic-tool-execution part. After the
baseline admission, route paired runtime observations to `aoa-evals` for a
bounded verdict; do not infer promotion from SDK validation.

## Verification

Run the part-focused contract tests, SDK mechanics topology and source
topology checks, full SDK tests, and the paired runtime-part validation.
