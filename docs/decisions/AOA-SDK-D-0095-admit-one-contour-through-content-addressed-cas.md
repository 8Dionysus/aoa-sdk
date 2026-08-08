# Admit One Contour Through Content-Addressed CAS

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0095
- Original date: 2026-08-08
- Surface classes: organ registry, contour admission, operator decision
- SDK facets: control-plane, compatibility, CLI
- Mechanic parents: boundary-bridge
- Guard families: contour isolation, content addressing, compare and swap, owner boundary, fail closed
- Posture: accepted protocol-independent control-plane contract

## Context

Registry v2 made `(organ_id, contour_id)` the admission identity, while the
existing resumable admission authorization still targeted one v1 organ-level
record. The deployed KAG canary exposed that using the old direct mutation
script would bypass the contour CAS and make a runtime observation stand in for
separate proof, acceptance, rollback, and operator authority.

## Options Considered

- Continue mutating v2 records through an operator-local script.
- Reuse v1 organ authorization and reinterpret its target as a contour.
- Add a content-addressed contour revision that consumes independently issued
  receipts and can only transition one exact shadow predecessor.

## Decision

Choose the third option.

`aoa_organ_contour_admission_revision_v1` names one organ and contour, carries
the expected predecessor digest, and is itself content-addressed. A separate
operator decision binds that predecessor. The revision must carry current
owner-qualified evidence for every required maturity axis, one compatible
consumer, central proof, owner acceptance, rollback readiness, owner freshness,
and a distinct last-good target.

The SDK validates issuer roles and evidence lifetimes, rejects a stale or
changed predecessor, keeps `cross_organ_proven` unasserted, and fixes effect and
rollback-execution authority to false. It returns a candidate registry source;
it does not publish that source, execute owner tools, infer acceptance, execute
rollback, or activate effects.

## Consequences

- V1 organ authorization no longer needs to be stretched across a different
  identity model.
- Runtime identity overlays remain non-admitting; admission consumes them only
  after stronger owners issue their own receipts.
- Short-lived evidence produces a short-lived admitted contour and therefore
  creates an explicit Keeper refresh obligation.
- Production publication remains a separate operator-controlled CAS and
  postcondition step.

## Source Surfaces

- `src/aoa_sdk/contracts/organ_registry_v2.py`
- `src/aoa_sdk/organs/registry_v2.py`
- `src/aoa_sdk/cli/organs.py`
- `mechanics/boundary-bridge/parts/organ-access-control-plane/`

## Follow-Up Route

Let `abyss-stack` compose a revision only from exact owner-issued evidence and
an explicit operator receipt. Admission Keeper automation may refresh invalid
nodes but cannot issue proof, acceptance, rollback, or operator decisions.

## Verification

Run schema parity, focused CAS/owner/expiry negative tests, mypy, ruff,
decision-index parity, and the repository release gate.
