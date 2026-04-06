# Session Closeout

`aoa-sdk` owns the control-plane helper for reviewed session closeout. It does
not invent skill meaning or proof logic. It only coordinates already-owned
publisher scripts and the existing `aoa-stats` refresh loop through one
manifest-driven handoff.

## Why this exists

By April 6, 2026 the federation already had:

- owner-local live receipt publishers in `aoa-skills`, `aoa-evals`,
  `aoa-playbooks`, `aoa-techniques`, and `aoa-memo`
- an automatic `aoa-stats` watcher that rebuilds live summaries when those logs
  change

The missing seam was one bounded operator-facing closeout path that can turn a
reviewed session into:

1. receipt publication into owner-local logs
2. deterministic `aoa-stats` refresh
3. one machine-readable closeout report and queueable audit trail
4. one inbox file that can be auto-processed by a user-level path watcher
5. one canonical closeout manifest assembled from a reviewed artifact and ready receipt paths

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
    },
    {
      "publisher": "aoa-playbooks.reviewed-run",
      "input_paths": [
        "receipts/playbook_review_harvest_receipt.json"
      ]
    },
    {
      "publisher": "aoa-techniques.promotion",
      "input_paths": [
        "receipts/technique_promotion_receipt.json"
      ]
    },
    {
      "publisher": "aoa-memo.writeback",
      "input_paths": [
        "receipts/memo_writeback_receipt.json"
      ]
    }
  ]
}
```

`input_paths` may be absolute or relative to the manifest file.

## Build request shape

Use the builder when an outer review wrapper already has a reviewed artifact and
owner-local receipt files, but should not hand-author the final closeout
manifest JSON.

```json
{
  "schema_version": 1,
  "closeout_id": "closeout-2026-04-06-session-growth",
  "session_ref": "session:2026-04-06-session-growth",
  "reviewed": true,
  "reviewed_artifact_path": "notes/reviewed_session_artifact.md",
  "trigger": "reviewed-closeout",
  "audit_refs": [
    "notes/route_summary.md"
  ],
  "batches": [
    {
      "publisher": "aoa-skills.session-harvest-family",
      "input_paths": [
        "receipts/harvest_packet_receipt.json"
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

The builder canonicalizes all paths to absolute form, injects the reviewed
artifact into `audit_refs`, writes the resulting manifest under
`.aoa/closeout/manifests/`, and can immediately enqueue it for automatic inbox
processing.

## Commands

Run one manifest directly:

```bash
aoa closeout run /srv/path/to/closeout.json --root /srv/aoa-sdk --json
```

Queue one reviewed manifest into the canonical inbox:

```bash
aoa closeout enqueue-current /srv/path/to/closeout.json --root /srv/aoa-sdk --json
```

Build one canonical manifest from a reviewed closeout request and enqueue it:

```bash
aoa closeout build-manifest /srv/path/to/closeout.request.json \
  --root /srv/aoa-sdk \
  --enqueue \
  --json
```

Process the canonical queue under `aoa-sdk/.aoa/closeout/`:

```bash
aoa closeout process-inbox /srv/aoa-sdk --json
```

Inspect the queue state:

```bash
aoa closeout status /srv/aoa-sdk --json
```

The queue layout is:

- `.aoa/closeout/inbox/`
- `.aoa/closeout/processed/`
- `.aoa/closeout/failed/`
- `.aoa/closeout/reports/`

Install the user-level inbox watcher when the machine should auto-process new
reviewed manifests as soon as they land in the canonical inbox:

```bash
python /srv/aoa-sdk/scripts/install_closeout_units.py --overwrite --enable
```

The watcher uses `aoa-closeout-inbox.path` to watch
`.aoa/closeout/inbox/*.json` and runs `aoa-closeout-inbox.service`, which calls
the bounded inbox processor script under `scripts/process_closeout_inbox.py`.

This makes the closeout step easy to automate from any outer session wrapper
without hiding ownership inside the SDK itself: wrappers enqueue reviewed
manifests, the inbox watcher processes them, and `aoa-stats` is refreshed only
through the existing source-owned publisher spine.
