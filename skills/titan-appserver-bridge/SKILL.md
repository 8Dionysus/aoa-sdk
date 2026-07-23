---
name: titan-appserver-bridge
description: Titan bridge event normalization or visible replay; for queue or gate decisions use titan-console; never live steering.
---

# titan-appserver-bridge

Operate inspectable bridge and replay helper state. The SDK can shape and
validate visible events; it cannot send them to Codex, steer a live session,
or recover hidden reasoning.

## Owner-source return

Resolve the canonical `aoa-sdk` root before owner reads:

1. Record `<bundle_dir>` from this loaded `SKILL.md`.
2. Inspect only `<bundle_dir>/.aoa-skill-source.json`. If present, require
   `aoa_skill_source_receipt_v1`, bundle `titan-appserver-bridge`, owner
   `aoa-sdk`, valid absolute `owner_root`, safe `source_path`, and matching
   owner `SKILL.md`. A malformed present handle is terminal.
3. Only when absent, run
   `git -C <bundle_dir> rev-parse --show-toplevel`.
4. Later read only `<owner_root>/skills/port.manifest.json`; require owner
   `aoa-sdk`, this bundle, and path `skills/titan-appserver-bridge`.
5. Stop `blocked_missing_owner_source` on mismatch. Do not discover another
   checkout.

## Select exactly one mode

Read `references/contract.yaml`, then only the selected procedure:

| Mode | Select when | Read |
|---|---|---|
| `bridge` | A visible app-server bridge session, JSON-RPC event set, or metrics packet must be normalized or inspected. | `references/bridge.md` |
| `event-replay` | Bridge events or an explicitly visible Codex session export must be replayed into derived state. | `references/event-replay.md` |

For a multi-stage request, create only the necessary task-local edges and load
the second mode after the first produces its typed output.
An isolated approval queue status or decision belongs to
`titan-console/approval-queue`; do not load this bundle only to interpret that
queue entry.
An isolated Forge or Delta gate decision for a bridge ledger belongs to
`titan-console/approval-witness`.

## Common contract

- Require explicit Titan intent, bounded source files, and visible event
  provenance.
- Treat `emit` output as a local unsent event witness.
- Treat bridge approval decisions as witness data requiring an external
  operator decision ref; this bundle does not authenticate approval.
- Preserve event gaps, ordering uncertainty, source kind, and replay limits.
- Return `titan-bridge-result-v1`: mode, source return, visible sources,
  helper actions, derived artifacts, transport and execution states, actual
  effects, verification, next owner route, and stop line.
- Before the final response, materialize every required
  `output_abi.required` key from `references/contract.yaml`. A shortened
  summary must not be labelled `titan-bridge-result-v1`.

## Stop

Stop after one validated bridge or replay result, truthful no-change, owner
handoff, or explicit blocker. Sending, live steering, runtime execution,
hidden transcript access, proof, and durable memory stay outside this skill.
