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
6. one canonical request assembled from a reviewed artifact and receipt bundle without hand-authoring JSON
7. one explicit split between detail skill receipts and generic project-core kernel receipts so one receipt file never mixes publisher families
8. one kernel-aware next-step brief in the closeout report after owner-local publication and stats refresh

## Boundary

- The closeout helper is manifest-driven, not heuristic.
- It only runs on `reviewed: true` manifests.
- It calls owner-owned publisher scripts instead of reimplementing their
  meaning in the SDK.
- It refreshes `aoa-stats` after receipt publication.
- It reads the canonical project-core kernel surface from `aoa-skills` and
  writes one deterministic next-step brief into each non-audit closeout report.
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
      "publisher": "aoa-skills.core-kernel-applications",
      "input_paths": [
        "receipts/core_skill_application_receipt.json"
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
      "publisher": "aoa-skills.core-kernel-applications",
      "input_paths": [
        "receipts/core_skill_application_receipt.json"
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

One receipt file must stay inside one publisher family. For kernel skills this
means detail receipts such as `harvest_packet_receipt` and generic
`core_skill_application_receipt` receipts live in separate files so the closeout
spine can route them into separate owner-local logs.

## Reviewed submission flow

When the outer session layer already has a reviewed artifact plus emitted owner
receipts, the highest-level control-plane entrypoint is:

```bash
aoa closeout submit-reviewed /srv/path/to/reviewed_session_artifact.md \
  --session-ref session:2026-04-06-session-growth \
  --receipt-dir /srv/path/to/receipts \
  --audit-ref /srv/path/to/route_summary.md \
  --root /srv/aoa-sdk \
  --json
```

`submit-reviewed` does four bounded things:

1. validates the reviewed artifact exists
2. groups receipt files by owner-local publisher using explicit receipt `event_kind`
3. writes a canonical request under `.aoa/closeout/requests/`
4. builds the manifest and, by default, enqueues it for the existing inbox watcher

This keeps the control plane explicit without forcing outer wrappers to
hand-author request or manifest JSON.

When an outer reviewed wrapper does not own a receipt publisher yet, use
`--allow-empty` for an audit-only closeout:

```bash
aoa closeout submit-reviewed /srv/path/to/W4-closeout.md \
  --session-ref session:qwen-local-pilot-v1:W4:closeout \
  --audit-ref /srv/path/to/W4-closeout.json \
  --trigger runtime-wave-closeout \
  --allow-empty \
  --root /srv/aoa-sdk \
  --json
```

Audit-only closeouts still produce the canonical request, manifest, queue item,
and report trail, but they do not invoke owner-local publishers and they skip
the stats refresh step on purpose.

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

Submit one reviewed artifact plus receipt bundle directly:

```bash
aoa closeout submit-reviewed /srv/path/to/reviewed_session_artifact.md \
  --session-ref session:2026-04-06-session-growth \
  --receipt-dir /srv/path/to/receipts \
  --root /srv/aoa-sdk \
  --json
```

Submit one reviewed artifact without a receipt bundle yet:

```bash
aoa closeout submit-reviewed /srv/path/to/W4-closeout.md \
  --session-ref session:qwen-local-pilot-v1:W4:closeout \
  --audit-ref /srv/path/to/W4-closeout.json \
  --allow-empty \
  --root /srv/aoa-sdk \
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

`aoa closeout status` now discloses both request and manifest surfaces so an
operator can tell whether the seam is failing before or after manifest
assembly.

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

## Kernel-aware brief

For non-audit closeouts, the SDK now adds `kernel_next_step_brief` to the JSON
report and to the human CLI output of `aoa closeout run` and
`aoa closeout process-inbox`.

The brief stays bounded:

- kernel order comes from `aoa-skills.project_core_skill_kernel.min`
- current-session skill coverage comes from the current closeout receipt batch
- usage counts come from refreshed `aoa-stats.core_skill_application_summary.min`

This keeps the next-step suggestion subordinate to source-owned kernel and
stats surfaces instead of hard-coding a second hidden router in the SDK.
