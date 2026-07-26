# Owner-Bounded Organ Access Control Plane

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0075
- Original date: 2026-07-25
- Surface classes: control-plane contract, private registry, discovery, activation plan
- SDK facets: control-plane, workspace discovery, compatibility, MCP projection
- Mechanic parents: codex-projection, boundary-bridge
- Guard families: deny-by-default admission, owner boundary, generated parity, rollback
- Posture: accepted target and transition architecture

## Context

OS Abyss has multiple direct MCP access planes, but consumer configuration is
currently a second, implicit registry. Package, deployed service, endpoint,
and Codex registration state can drift independently. An always-loaded
consumer catalog also spends context before task intent is known, while a
successful list or call says nothing about provenance, freshness, effects, or
owner acceptance.

The center organ contract now requires deny-by-default admission and explicit
source, access, control-plane, runtime, proof, and acceptance owners. The
stronger-owner evidence is the landed `Agents-of-Abyss` organ contract and
decision `AOA-CENTER-D-0032` at revision
`d7b1e46d6fa240416f9253f099a516da9fc5a53b`. The SDK already owns
runtime-neutral control-plane models, workspace discovery, compatibility
helpers, and the accepted routing succession. It is therefore the narrowest
owner for a typed organ registry and progressive discovery, but not for
runtime execution or owner meaning.

## Options Considered

- Treat Codex MCP configuration as the registry and add more static entries.
- Put registry, discovery, owner proxying, and runtime execution into an
  `abyss-stack` gateway.
- Let `aoa-sdk` own a protocol-independent registry source contract,
  deterministic projection, discovery, compatibility comparison, and
  activation-plan compiler while direct owner adapters and runtime execution
  remain outside the SDK.

## Decision

Choose the third option.

`aoa-sdk` owns:

- versioned, strict models for organ identity, owner roles, capabilities,
  primitives, effect classes, freshness, revisions, compatibility, maturity,
  evidence refs, admission, activation preconditions, and rollback;
- the normative private-registry source contract and deterministic projection
  compiler;
- progressive discovery through catalog, organ inspection, capability
  inspection, compatibility checks, and activation-plan compilation;
- typed result-envelope metadata that wraps, but does not replace,
  owner-specific payload models;
- a protocol-independent adapter interface so stable and next MCP protocol
  pairs can coexist behind the same control-plane contracts.

The concrete private registry source is an explicit path selected by OS
workspace configuration. It is not discovered by scanning repositories,
processes, listeners, or Codex configuration. The OS workspace/operator owns
the instance values; `aoa-sdk` owns the schema and validation. Owner records,
stack runtime observations, proof evidence, and acceptance receipts enter only
as owner-qualified references.

The compiler emits a content-addressed, secret-free projection. Unknown or
invalid entries are denied. `suspended`, `deprecated`, and `retired` entries
cannot be activated. An observed endpoint or successful call cannot raise
admission or maturity without the required owner and proof evidence.

Discovery returns only the bounded metadata needed for the current step:

```text
catalog
  -> inspect organ
  -> inspect capability
  -> authorize and compile activation plan
  -> load selected schema
  -> host executes a direct owner route
  -> attach receipt
```

An activation plan is immutable candidate intent, not activation. It names the
exact organ, capability, effect family, credential class, schema identity,
precondition evidence, consumer, expiry, and rollback route. The host and
`abyss-stack` retain execution and lifecycle authority.

The target topology keeps direct owner adapters. The SDK discovery surface is
not a semantic gateway and does not proxy owner tools.

The transition starts with a shadow registry built from reviewed owner records
and the dated baseline, while existing direct MCP registrations remain live.
Consumers compare the registry projection with observed schemas before any
allowlist replaces a static catalog. One owner and one read capability advance
at a time. Broken, unproven, or unaccepted routes remain disabled or shadow.

The routing succession remains independent. `aoa-routing` is canonical until
the existing G5 owner-switch receipt; no separate long-lived
`aoa-routing-mcp` is introduced. Organ discovery may call the current routing
contract but cannot use SDK candidate output as proof that the owner switch
occurred.

Rollback disables activation in the private source, regenerates the
projection, restores the last-known-good direct consumer registration or
stable adapter, and asks the runtime owner to execute its rollback. Source
records and compatibility aliases remain until consumer-zero is proven.
Protocol rollback and authority rollback are separate operations.

## Rationale

The SDK can make access intent typed, inspectable, and transport-neutral
without becoming a daemon, a proof system, or a universal owner. An explicit
source path avoids magical discovery and makes every admission change
reviewable. A compiled plan preserves host authority and gives runtime
execution a stable, testable input.

Progressive discovery reduces context pressure while direct connections avoid
the authority and confused-deputy risks of a mega-gateway.

## Consequences

- Static consumer configuration becomes a generated or transitional
  projection rather than the admission source.
- Runtime and proof evidence need stable typed references.
- Consumers that cannot dynamically connect require a bounded allowlist
  fallback and explicit reload.
- The SDK must reject unknown fields, invalid state transitions, unqualified
  evidence, and higher-effect activation without the required policy posture.
- Registry freshness and observed-schema drift become explicit failure states.
- Executing activation, lifecycle, source writes, durable memory, verdicts,
  and external effects remains outside the SDK.

## Source Surfaces

- `DESIGN.md`
- `docs/boundaries.md`
- `src/aoa_sdk/contracts/control_plane.py`
- `8Dionysus/Agents-of-Abyss@d7b1e46d6fa240416f9253f099a516da9fc5a53b:docs/organ-contract/ORGAN_CONTRACT.md`
- `8Dionysus/Agents-of-Abyss@d7b1e46d6fa240416f9253f099a516da9fc5a53b:docs/decisions/AOA-CENTER-D-0032-organ-access-admission-law.md`

## Follow-Up Route

Implement the strict organ-access models, schema, registry compiler,
progressive discovery API, envelope metadata, and activation-plan validation
under the SDK source lane. Localize consumer projection mechanics under
Codex Projection. Route runtime observations and execution to `abyss-stack`,
central proof to `aoa-evals`, owner payloads to each organ, and routing
authority through the existing succession gates.

## Verification

Use the decision index validator, root source/release validation, focused
contract tests, schema parity, negative admission tests, and a shadow-registry
consumer comparison before any runtime activation.
