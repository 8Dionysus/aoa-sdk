# Session Closeout

`aoa-sdk` owns the control-plane helper for reviewed session closeout. It does
not invent skill meaning or proof logic. It only coordinates already-owned
publisher scripts and the existing `aoa-stats` refresh loop through one
manifest-driven handoff.

## Why this exists

By April 6, 2026 the federation already had:

- owner-local live receipt publishers in `aoa-skills` and `aoa-evals`
- an automatic `aoa-stats` watcher that rebuilds live summaries when those logs
  change

The missing seam was one bounded operator-facing closeout path that can turn a
reviewed session into:

1. receipt publication into owner-local logs
2. deterministic `aoa-stats` refresh
3. one machine-readable closeout report and queueable audit trail

## Boundary

- The closeout helper is manifest-driven, not heuristic.
- It only runs on `reviewed: true` manifests.
- It calls owner-owned publisher scripts instead of reimplementing their
  meaning in the SDK.
- It refreshes `aoa-stats` after receipt publication.
- It does not silently invoke Codex skill reasoning, rewrite proof meaning, or
  replace source-owned truth.

## Manifest shape

```json
{
  "schema_version": 1,
  "closeout_id": "closeout-2026-04-06-session-growth",
  "session_ref": "session:2026-04-06-session-growth",
  "reviewed": true,
  "trigger": "reviewed-closeout",
  "audit_refs": [
    "notes/reviewed_session_artifact.md"
  ],
  "batches": [
    {
      "publisher": "aoa-skills.session-harvest-family",
      "input_paths": [
        "receipts/harvest_packet_receipt.json",
        "receipts/progression_delta_receipt.json"
      ]
    },
    {
      "publisher": "aoa-evals.eval-result",
      "input_paths": [
        "receipts/eval_result_receipt.json"
      ]
    }
  ]
}
```

`input_paths` may be absolute or relative to the manifest file.

## Commands

Run one manifest directly:

```bash
aoa closeout run /srv/path/to/closeout.json --root /srv/aoa-sdk --json
```

Process the canonical queue under `aoa-sdk/.aoa/closeout/`:

```bash
aoa closeout process-inbox /srv/aoa-sdk --json
```

The queue layout is:

- `.aoa/closeout/inbox/`
- `.aoa/closeout/processed/`
- `.aoa/closeout/failed/`
- `.aoa/closeout/reports/`

This makes the closeout step easy to automate from any outer session wrapper
without hiding ownership inside the SDK itself.
