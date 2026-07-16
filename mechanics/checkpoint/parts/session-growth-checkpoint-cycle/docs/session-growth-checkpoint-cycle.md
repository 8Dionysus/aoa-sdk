# Session Growth Checkpoints

`aoa-sdk` owns a session-local checkpoint control plane. It preserves
intermediate evidence, requires semantic review, materializes reviewed evidence,
and moves closed scopes without becoming a skill runtime, memory owner, proof
owner, or cross-repository workflow runner.

## Boundary

- `aoa checkpoint mark`, `append`, `after-commit`, and `review-note`
  are the explicit capture and review routes.
- `aoa surfaces detect --phase checkpoint` may add advisory owner candidates;
  it does not select or execute skills.
- Post-commit capture reads an existing host runtime identity. It never creates
  an SDK skill session merely to make a checkpoint possible.
- A captured commit begins with `agent_review=pending`. Git boundary checks,
  closeout-context assembly, materialization, and lifecycle closure fail closed
  while required semantic review remains pending.
- `review-note --auto` may lift the matching bounded auto-observation into a
  reviewed note. It remains a session-local review, not owner acceptance.
- `build-closeout-context` aggregates reviewed notes and exact evidence refs
  for one host-identified runtime scope. It fails before writing when runtime
  identity is unavailable.
- `materialize-closeout-handoff` writes a reviewed evidence bundle,
  materialization receipt, and, when candidates exist, an explicit owner
  handoff. Every output keeps `capability_execution_claimed=false`.
- No checkpoint command invokes inferred sibling publishers, refreshes owner
  stats, chooses a next skill, or claims that a capability ran.
- `lifecycle-audit`, `backlog-audit`, `close-archive`,
  `reconcile-sessions`, and `sweep-closed-sessions` preserve the distinction
  between pending review, reviewed materialization, closed evidence, stale
  evidence, and a session that ended without reviewed closeout.
- aoa-session-memory refs are read-only evidence coordinates. The SDK does not
  mutate session memory or promote its interpretation.

## Runtime Identity

Checkpoint scope comes from host-provided runtime evidence such as
`CODEX_THREAD_ID`, an explicit runtime metadata file, or compatible host
metadata. The public file option is `--runtime-session-file`.

Legacy `.aoa/skill-runtime-session.json` and
`.aoa/skill-runtime-sessions/*.json` files may still be classified as
`legacy-skill-session` evidence when supplied explicitly. They are read-only
compatibility inputs, not current runtime authority, and are never created or
repaired by the SDK.

A mismatch between explicit thread identity and runtime metadata is a conflict,
not permission to merge two sessions. A post-commit report is trace evidence,
not a runtime session.

## Local Storage

The active ledger lives under:

```text
aoa-sdk/.aoa/session-growth/current/<runtime-session-id>/<repo-label>/
  checkpoint-note.jsonl
  checkpoint-note.json
  checkpoint-note.md
  post-commit-report.json
  closeout-context.json
  CHECKPOINT_CLOSEOUT_EVIDENCE_BUNDLE.json
  CHECKPOINT_CLOSEOUT_MATERIALIZATION_RECEIPT.json
```

Owner-candidate handoffs remain SDK-local routing material under the checkpoint
closeout area. Archived scopes move under
`.aoa/session-growth/archive/`; append-only JSONL evidence is preserved.

The unscoped `current/<repo-label>/` form is quarantined legacy evidence for a
note without runtime identity. New mutable routes never create it and it must
not silently attach to a different live thread.
Closed or promoted scopes are archived before a new cycle reuses their repo
label.

## Lifecycle

1. Capture a bounded checkpoint event.
2. Review every pending semantic observation.
3. Build one closeout context for the matching runtime scope.
4. Materialize the reviewed evidence and owner candidates.
5. Let each owner workflow decide whether to execute, accept, or reject the
   candidate.
6. Close and archive the SDK-local scope only after review and materialization
   requirements are satisfied.

A session-memory-backed session end without reviewed closeout may be archived
as `archived_without_closeout`. That state does not mean `closed` and does
not invent a missing review or execution.

Nonpending stale scopes may be archived as stale evidence. Pending-review scopes
remain blocked even when nearby artifacts look complete.

## Candidate And Carrier Intelligence

`candidate-intelligence` and `carrier-intelligence` derive navigation from
checkpoint action facets. They may expose repeated signatures, wrapper gaps,
owner pressure, or possible mechanic/tool/MCP/hook/script/service/index
carriers.

These outputs are generated review aids only. They do not admit a skill,
playbook, technique, eval, memo entry, mechanic, tool, MCP, hook, daemon,
service, generated index, RAG layer, or owner verdict. A single weak event
cannot become an accepted carrier.

## Executable Route

Root `AGENTS.md#inspection-and-checkpoint-loop` owns the compact operator
commands. This part's `VALIDATION.md` owns focused manual lifecycle and
regression routes. Use current CLI help for exact optional flags; this design
note does not duplicate executable command truth.

## Verification Posture

Manual lifecycle trials are the behavioral authority. A retained regression may
only encode an invariant already observed in a real current, pending, reviewed,
materialized, conflict, legacy-evidence, close/archive, or no-closeout trial.

Tests and validators must not replace the reviewed artifact with synthetic green
status, infer capability execution from receipt presence, or mock removed owner
publishers back into existence.

## Promotion Read

`aoa checkpoint promote` remains an explicit, review-gated local handoff. It
does not turn checkpoint notes into memory, proof, progression, quest, stats, or
owner truth. Surviving evidence must enter the receiving owner's own admission
route.
