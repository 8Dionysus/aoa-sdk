# Explicit Intent And Consumed Surface Inputs

## Status

Accepted for the bounded SDK simplification. Local source implementation does
not establish installation, runtime adoption, or owner acceptance of candidates.

## Index Metadata

- Decision ID: AOA-SDK-D-0108
- Original date: 2026-09-07
- Surface classes: API, owner boundary, compatibility
- SDK facets: control-plane, facade boundary, runtime entry
- Mechanic parents: boundary-bridge, checkpoint
- Guard families: owner authority, intent attribution, non-execution
- Posture: accepted

## Context

Word matching treated a layer name as a high-confidence explicit request.
Negations, quotes, and examples could therefore acquire the same signal as an
operator request, while a positive request in another language could disappear.
The checkpoint fallback repeated that positive inference. Similar substring
logic treated `new wrapper` as novelty and `summary` as stats consumption.
The packets did not execute actions, but they generated unsupported pressure.

## Options Considered

- Retain lexical positive authority and patch individual phrases.
- Require a new model service for every detection call.
- Keep weak lexical navigation and accept explicit, caller-interpreted inputs.

## Decision

Choose explicit caller input without a new mandatory model dependency.
Lexical items retain existing owner handles but have low confidence, empty
signals, no harvest/promotion hints, and no positive checkpoint event. Exact
`requested_owner_layers` and `declared_signals` carry caller interpretation,
not a claim of execution or verified occurrence.

Wrapper novelty requires a non-empty caller reason keyed to an observed action
signature. Words cannot override strong existing fit; a reason can yield only
an unreviewed candidate and cannot affect other signatures.

Stats regrounding requires exact declared consumed surface refs. The existing
coverage/risk rule stays in force after selection. A missing or incompatible
declared dependency is an error, not an empty clear result. The former intent
entrypoint remains callable but no longer selects from prose.

## Rationale

The caller already interprets the current request. The SDK should preserve that
interpretation across its typed boundary rather than independently inventing
operator will from tokens. Catalog handles remain available for inspection;
language support does not require a growing negation dictionary.

## Consequences

- Existing callers that need positive signals must supply explicit assertions.
- The serialized report shape and non-execution guarantees remain compatible.
- Restrictive risk suspicion remains advisory; fit/readiness scoring is a
  separate review topic, not measured safety established by this change.
- Existing checkpoint notes, generated indexes, and owner candidate queues are
  not automatically rewritten, accepted, rejected, or deleted.
- Sibling owners retain proof, memory, role, routing, stats, and capability meaning.

## Source Surfaces

- `src/aoa_sdk/surfaces/`
- `src/aoa_sdk/checkpoints/candidate_intelligence.py`
- `src/aoa_sdk/checkpoints/registry.py`
- `src/aoa_sdk/stats/regrounding.py`
- `src/aoa_sdk/stats/registry.py`
- `src/aoa_sdk/cli/surfaces.py`
- `src/aoa_sdk/cli/checkpoint.py`

## Follow-Up Route

Owner-layer signal handoff and checkpoint contracts own caller migration.
Future readiness changes need their own evidence and decision; no new universal
intent classifier, scoring system, or candidate registry is introduced here.

## Verification

Use `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/VALIDATION.md`,
the checkpoint part tests, the stats reader tests, and root `VALIDATION.md`.
Regressions cover negative/quoted/multilingual input, explicit API and CLI
requests, no positive lexical fallback, exact consumed refs, and signature-local
novelty. Decision indexes are derived with the owner builder.
