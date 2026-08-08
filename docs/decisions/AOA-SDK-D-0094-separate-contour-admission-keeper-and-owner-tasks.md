# Separate Contour Admission, Keeper Evidence, and Owner Tasks

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0094
- Original date: 2026-08-08
- Surface classes: organ registry, admission maintenance, durable task control
- SDK facets: control-plane, compatibility, CLI
- Mechanic parents: boundary-bridge
- Guard families: contour isolation, content addressing, compare and swap, owner boundary, fail closed
- Posture: accepted protocol-independent control-plane contract

## Context

The v1 organ registry admitted one endpoint per organ, admission evidence could
only be replayed manually, and long-running owner work had no shared durable
handle below MCP. That shape cannot represent separate read, candidate,
proof-result, and effect credentials, cannot renew only invalidated evidence,
and risks making an experimental wire extension the owner of task truth.

## Options Considered

- Keep one organ-level record and treat additional processes as deployment
  detail.
- Put admission renewal and durable task state directly into MCP servers.
- Give the SDK protocol-independent contour, Keeper, and TaskStore mechanics
  while retaining evidence issuance, execution, proof, acceptance, and registry
  writes at their existing owners.

## Decision

Choose the third option.

Registry v2 addresses admission by `(organ_id, contour_id)`. Credential,
principal, allowlist, endpoint, runtime identity, evidence, currentness,
rollback, and last-good state remain independent per contour. V1 migration
preserves claims and expiry; owner supplements may add only new shadow shapes,
and runtime overlays may correct evidenced identity without refreshing
admission, proof, or acceptance.

Admission Keeper specs form an ordered dependency graph. Immutable
content-addressed nodes are reusable only when stage input, owner, subject,
dependencies, outcome, and expiry still match. A cycle imports owner-issued
nodes, emits an incremental plan, and CAS-publishes a new state under one
exclusive store lock spanning the complete transaction, so simultaneous event
and timer triggers cannot both win the same prior-state boundary. Keeper and
TaskStore roots, internal directories, and opened lock descriptors reject
symlink substitution. The Keeper never runs owner tools or issues stronger
owner verdicts.

The file TaskStore persists a principal-bound owner task before returning its
opaque random ID. Every transition is CAS-checked, reauthorized, audited, and
bounded by TTL, quota, and payload limits. Task identity is not admission
identity and is not authorization.

## Consequences

- Read admission cannot authorize candidate, proof-result, or effect contours.
- Expired specs and evidence produce explicit blocked plans and states rather
  than timestamp extension or an exception-only failure.
- Unchanged renewal can reuse valid nodes; changed subjects invalidate only
  dependent stages.
- Concurrent Keeper triggers serialize without lost CAS updates, and unsafe
  storage indirection fails closed before evidence or task state is read.
- MCP Tasks may later adapt the TaskStore, but cannot become owner truth.
- A live runtime still needs external owner, proof, acceptance, consumer, and
  registry evidence before it is current or admitted.

## Source Surfaces

- `src/aoa_sdk/contracts/organ_registry_v2.py`
- `src/aoa_sdk/organs/registry_v2.py`
- `src/aoa_sdk/contracts/admission_keeper.py`
- `src/aoa_sdk/organs/admission_keeper.py`
- `src/aoa_sdk/contracts/tasks.py`
- `src/aoa_sdk/organs/task_store.py`
- `src/aoa_sdk/cli/organs.py`
- `mechanics/boundary-bridge/parts/organ-access-control-plane/`

## Follow-Up Route

Let `abyss-stack` consume these mechanics through exact package evidence and
private state. Owner validators issue their own nodes. `aoa-evals`, acceptance
owners, consumers, and the registry operator retain their independent gates.
Any MCP Tasks adapter remains feature-gated until actual client capability and
extension lifecycle proof exist.

## Verification

Run schema parity, focused organ-control tests, mypy and ruff over the new
contracts, decision-index parity, and the repository release gate.
