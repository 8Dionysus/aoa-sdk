# Session Closeout

`aoa-sdk` owns the control-plane helper for reviewed session closeout. It does
not invent skill meaning or proof logic. It only coordinates already-owned
publisher scripts and the existing `aoa-stats` refresh loop through one
manifest-driven handoff.
The explicit checkpoint-to-closeout bridge now sits beside this seam and
prepares local reviewed-closeout artifacts and receipts without publishing them
or refreshing stats on its own.

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
9. one optional reviewed reference back to a local checkpoint note when the
   session already accumulated checkpoint-aware pre-harvest context

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
- `aoa closeout run` does not auto-run `aoa-checkpoint-closeout-bridge`.
- `aoa surfaces handoff` is reviewed-only and remains separate from this closeout runner.
- `closeout-context.json` may carry `candidate_lineage_map` and
  `owner_followthrough_map`, plus one `followthrough_decision`, but all three stay reviewed-only advisory surfaces
  rather than owner truth.

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

Build one explicit checkpoint-to-closeout evidence bundle without publishing
anything yet:

```bash
aoa checkpoint build-closeout-context /srv/aoa-sdk \
  --reviewed-artifact /srv/path/to/reviewed_session_artifact.md \
  --root /srv/aoa-sdk \
  --json
```

When a matching active runtime session exists, this builder aggregates every
repo-scoped checkpoint ledger under
`aoa-sdk/.aoa/session-growth/current/<runtime-session-id>/` before it derives
the closeout candidate map. The reviewed artifact remains the primary reread
source, and the repo-root checkpoint note must still match the resolved
reviewed session or the closeout fails closed.
Legacy unscoped ledgers stay eligible only when they are migration-safe for the
same runtime session; if one explicitly points at a different runtime session,
the builder archives it out of `current/` before continuing so the live closeout
scope stays unambiguous.
That same bundle may now emit a sibling `owner_followthrough_map` which points
toward the next owner-status surface and requested decision class without
minting `candidate_ref`, `seed_ref`, or `object_ref`.
In other words, reviewed closeout may point toward the next tracked owner move
without minting `candidate_ref`, `seed_ref`, or `object_ref`.
When the active runtime session also exposes a live Codex rollout path, the
builder now binds that session trace into the context so reviewed closeout can
reread the whole runtime thread instead of only the reviewed artifact plus one
narrow checkpoint ledger.

Execute the explicit reviewed-closeout skill chain without publishing or
refreshing stats:

```bash
aoa checkpoint execute-closeout-chain /srv/aoa-sdk \
  --reviewed-artifact /srv/path/to/reviewed_session_artifact.md \
  --root /srv/aoa-sdk \
  --json
```

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

When a local checkpoint note exists, reviewed surface closeout handoff may also
preserve `checkpoint_note_ref` and `surviving_checkpoint_clusters` so closeout
does not have to reconstruct checkpoint survivors from raw append history.
The explicit `aoa-checkpoint-closeout-bridge` should consume those reviewed
surfaces as hints, but it must still reread the reviewed artifact and any
receipt evidence before donor harvest, progression lift, and quest harvest run.

Install the user-level inbox watcher when the machine should auto-process new
reviewed manifests as soon as they land in the canonical inbox:

```bash
python /srv/aoa-sdk/scripts/install_closeout_units.py --overwrite --enable
```

## Surface detection handoff

First-wave surface detection is a separate, additive seam.

- `aoa closeout run` does not auto-run `aoa surfaces handoff`
- `aoa surfaces handoff` is reviewed-only and writes into `.aoa/surface-detection/`
- surviving surface notes keep their truth labels; the handoff does not promote
  anything by itself

Use the separate handoff when a reviewed session should preserve surface
observations for the session-growth kernel without pretending those owner-layer
candidates were activated:

```bash
aoa surfaces handoff /srv/aoa-sdk/.aoa/surface-detection/aoa-sdk.closeout.latest.json \
  --session-ref session:2026-04-07-surface-first-wave \
  --reviewed \
  --root /srv/aoa-sdk \
  --json
```

For the first-wave boundary, second-wave enrichments, heuristics, and target
selection rules, use `docs/aoa-surface-detection-closeout-handoff.md` and
`docs/aoa-surface-detection-second-wave.md`.

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

## Owner follow-through handoff

When a reviewed closeout already reaches owner-layer follow-through, the SDK
now also writes a persistent owner handoff bundle under:

- `.aoa/closeout/handoffs/`

This handoff stays separate from the kernel brief.
The kernel brief answers "what core skill comes next, if any?"
The owner handoff answers "what owner-layer artifact should be drafted or
authored next?"

The current bounded sources are:

- `harvest_packet_receipt`
  - when the receipt points to a readable `HARVEST_PACKET`, accepted candidates
    become `draft-owner-artifact` handoffs
- `quest_promotion_receipt`
  - closed promotion verdicts become `author-owner-artifact` handoffs

This gives later sessions one persistent queue-like surface so a strong harvest
does not stop at "result + analysis" and quietly lose the next authoring move.
