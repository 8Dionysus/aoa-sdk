# Host-Visible Cross-Organ Orchestration

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0080
- Original date: 2026-07-26
- Surface classes: control-plane contract, cross-organ orchestration, receipt chain
- SDK facets: control-plane, CLI, boundary bridge
- Mechanic parents: boundary-bridge
- Guard families: owner boundary, freshness, effect ceiling, receipt binding, no execution
- Posture: accepted source candidate

## Context

OS Abyss needs reproducible flows that can cross direct owner MCP access
planes. The first concrete chain is KAG evidence to a memo candidate, an eval
request and result, and an explicit owner acceptance decision. Existing owner
contracts already support their own bounded stage, but none should absorb the
other owners or coordinate hidden writes.

Direct server-to-server chaining would hide credentials, effects, failures,
and intermediate evidence from the OS host. Treating an eval result or model
confidence as acceptance would bypass the memory owner. Adding orchestration
to the workspace MCP would also collapse progressive discovery into ambient
execution pressure.

## Options Considered

- Let one MCP server invoke the remaining owners.
- Put a stateful semantic gateway in `abyss-stack`.
- Let `aoa-sdk` validate an immutable host-visible state machine while the
  host performs each direct owner call and supplies each receipt.

## Decision

Choose the third option.

`aoa-sdk` defines a strict five-stage request, typed artifact and schema
identities, host receipts, stage observations, immutable stages, and a
content-addressed run. Every request pins the current owner schema digest and
source revision. Every transition binds the previous snapshot, exact input,
exact output, owner evidence, freshness, effect state, receipt, and next
owner.

The SDK exposes start, single-stage advance, and full reconstruction through
`AoASDK.organs` and `aoa organs orchestration-*`. It never invokes an owner
tool. The state machine is not exposed through workspace MCP.

Stale or blocked evidence stops or denies the chain. Candidate stages cannot
claim durable effects. The final stage requires an explicit acceptance-owner
review and exact owner decision receipt. Model confidence is structurally
false as acceptance authority.

## Rationale

The SDK already owns transport-neutral control-plane handles and can validate
cross-object invariants without becoming a runtime or domain owner. Keeping
each owner call outside the SDK lets `abyss-stack` or another host preserve
credentials, timing, retries, authorization, and rollback as visible OS
actions.

## Consequences

- Cross-organ progress can be replayed and audited without hidden context.
- Owner schema or source drift blocks the next transition.
- KAG evidence cannot silently become memory.
- Eval results remain proof-owner artifacts and cannot imply consumer
  acceptance.
- Hosts must persist and pass one explicit run snapshot and observation per
  transition.
- The synthetic accepted fixture proves shape, not live owner acceptance.

## Source Surfaces

- `src/aoa_sdk/contracts/organ_orchestration.py`
- `src/aoa_sdk/organs/orchestration.py`
- `src/aoa_sdk/cli/organs.py`
- `mechanics/boundary-bridge/parts/cross-organ-orchestration/`
- `docs/decisions/AOA-SDK-D-0075-owner-bounded-organ-access-control-plane.md`
- `docs/decisions/AOA-SDK-D-0079-expose-organ-discovery-through-workspace-mcp.md`

## Follow-Up Route

Route host integration, owner calls, receipt issuance, credentials, lifecycle,
and rollback to `abyss-stack`. Route current source meaning to `aoa-kag`,
`aoa-memo`, and `aoa-evals`. Keep live MCP, acceptance, and benefit evidence
outside SDK source claims.

## Verification

Run the part-local schema/example parity, focused tests, mypy, mechanics
topology, decision-index, and root SDK validation routes. Live runtime evidence
remains a later stronger-owner gate.
