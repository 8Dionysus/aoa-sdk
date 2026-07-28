# Research Basis: KAG to Owner Acceptance

Research date: 2026-07-26.

## Method

The investigation used KAG for owner-qualified navigation, then returned every
substantive claim to the current owner checkout and exact source revision.
KAG search projection was stale or degraded during the investigation, so its
hits were not treated as current owner truth.

## Owner findings

### aoa-kag

Source revision:
`58ab52ffc06bab5cc28842a0b4336c6efa16b6ff`.

- `kag/LOCAL_SUBTREE_PROTOCOL.md` defines owner, provenance, freshness,
  builder, validator, storage, return-route, result, and fallback fields.
- `docs/decisions/AOA-KAG-D-0015-kag-mcp-retrieval-contract.md` keeps MCP output
  as qualified navigation evidence with trace and degradation metadata.
- `schemas/kag-mcp-result.schema.json` is the typed stage output. Its inspected
  SHA-256 is
  `1516bc25755b26c156a58709c5e7600e276daa21f115d7cdc61031cbd67162d5`.

Conclusion: KAG may supply evidence and provenance, but cannot write memory or
become source truth.

### aoa-memo

Source revision:
`e0d3653c11d948f962bcb033749c86c52388ec5f`.

- `docs/memory/LOCAL_MEMO_PORT_STANDARD.md` defines
  candidate -> receipt -> export -> reviewed owner route.
- `docs/boundaries/MEMORY_WRITE_PATH_GUARDRAILS.md` requires source refs,
  trust, lineage, review state, action split, and allowed result.
- `schemas/memory-ports/local_memo_candidate.schema.json` permits candidate
  preparation, not durable landing.
- `schemas/support-objects/reviewed_intake_landing_receipt.schema.json`
  represents the stronger reviewed owner result.

Conclusion: the orchestration may carry a memo candidate and a final reviewed
receipt, but it cannot promote the candidate automatically.

### aoa-evals

Source revision:
`4d03125d0961dbc0b15332f1a146cd0f7f08eb23`.

- `docs/architecture/AOA_EVALS_MCP_CONTRACT.md` permits selection, inspection,
  candidate preparation, and validation while retaining proof authority in
  owner source.
- `mechanics/proof-object/parts/eval-authoring/schemas/eval-need.schema.json`
  carries candidate evidence and source refs.
- `mechanics/publication-receipts/parts/receipt-payload/schemas/eval-result-receipt.schema.json`
  is explicitly weaker than the bundle/report it references and does not mean
  the consuming owner accepted a change.

Conclusion: eval request and result are separate stages; neither may mutate
memory or close owner acceptance.

## Architecture consequence

No examined owner should coordinate the whole chain. The narrow owner is an
`aoa-sdk` state-machine contract operated by the host. It validates order and
receipts without invoking MCP. `abyss-stack` is the intended OS host for
actual owner connections and receipt issuance, while every domain owner
retains meaning and acceptance.

This is a source-side architecture result. Live invocation, consumer
integration, benefit, owner acceptance, and rollback require separate runtime
evidence.
