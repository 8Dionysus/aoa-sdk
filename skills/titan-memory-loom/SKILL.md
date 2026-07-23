---
name: titan-memory-loom
description: Titan receipt ingest, candidate recall, or aoa-memo retention handoff; never generic or session memory.
---

# titan-memory-loom

Operate SDK-owned Titan memory helper shapes while keeping memory meaning and
retention authority in `aoa-memo`. Ingested records and recall results remain
candidates.

## Owner-source return

Resolve the canonical `aoa-sdk` root:

1. Record `<bundle_dir>` from this loaded `SKILL.md`.
2. Inspect only `<bundle_dir>/.aoa-skill-source.json`. If present, require
   schema `aoa_skill_source_receipt_v1` or
   `aoa_skill_source_receipt_v2`, bundle `titan-memory-loom`, owner `aoa-sdk`,
   version `0.1.1`, valid absolute `owner_root`, safe `source_path`, and
   matching owner `SKILL.md`. For v2 also require non-empty `digest`,
   `source_fingerprint`, `source_fingerprint_scope`, and
   `prompt_description_sha256`; preserve `capability_graph_hash` when present.
   A malformed present handle is terminal.
3. Only when absent, run
   `git -C <bundle_dir> rev-parse --show-toplevel`.
4. Later read only `<owner_root>/skills/port.manifest.json`; require owner
   `aoa-sdk`, this bundle, and path `skills/titan-memory-loom`.
5. Stop `blocked_missing_owner_source` on mismatch. Do not search for another
   checkout.

Report the receipt schema and v2 identity dimensions when present. They locate
and identify the installed source package; they do not prove durable memory,
helper execution, or current owner parity.

## Select exactly one mode

Read `references/contract.yaml`, then only the selected procedure:

| Mode | Select when | Read |
|---|---|---|
| `ingest` | A concrete Titan receipt witness should become a local candidate record. | `references/ingest.md` |
| `recall` | A concrete Titan candidate index must answer a bounded recall question. | `references/recall.md` |
| `retention-handoff` | A concrete Titan record may need masking, tombstoning, pruning, or retention review. | `references/retention-handoff.md` |

Do not use this bundle merely because a task mentions memory. First writeback
without a Titan record belongs to `aoa-memo-writeback`; raw `.aoa` evidence
belongs to the session-memory route.
A concrete local Titan receipt or index without raw `.aoa` input is a negative
trigger for session-memory routing; do not load that route merely to restate
this boundary.

## Common contract

- Require explicit Titan intent and concrete receipt, index, record, or
  retention target.
- Preserve record id, source refs, confidence, state, and authority warning.
- Never call the helper `redact` command in `retention-handoff`; it can mutate
  immediately and does not prove `aoa-memo` acceptance.
- Never report candidate ingestion or recall as durable memory or current
  owner truth.
- Return `titan-memory-result-v1`: mode, source return, target, source refs,
  candidate records, disposition, actual effects, verification, memo handoff,
  and stop line.
- Before the final response, materialize every required
  `output_abi.required` key from `references/contract.yaml` for each executed
  mode. A shortened summary must not be labelled `titan-memory-result-v1`.

## Stop

Stop after one validated local candidate operation, bounded recall,
effect-free retention handoff, owner handoff, or explicit blocker. Durable
memory, retention acceptance, source truth, and proof stay outside this skill.
