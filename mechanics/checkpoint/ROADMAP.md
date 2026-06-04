# Checkpoint Roadmap

Checkpoint is the SDK control panel for intermediate state: capture, review,
return, closeout context, and handoff. It makes session-local evidence easier
to inspect without turning checkpoints into memory, proof, progression, or
owner acceptance.

## Current Contour

- Keep session-growth capture, dirty-gate hook posture, review-note gates,
  reviewed session handoff runner behavior, child-task re-entry, and reviewed
  closeout context carry routed through active `parts/`.
- Keep checkpoint notes session-local until a reviewed promotion route accepts
  them.
- Keep reviewed handoff runner output operator-visible and evidence-linked, not
  an automatic closeout result.
- Keep reviewed closeout carry fields advisory and owner-routed.
- Keep `current/` lifecycle-visible: active runtime scopes stay current,
  pending-review scopes remain blocked, reviewed closeout execution can be
  closed and archived, and nonpending stale scopes can move to archive evidence
  without being marked as reviewed closeout.
- Keep no-closeout session endings visible: when aoa-session-memory has
  preserved the closed Codex session, checkpoint reconcile/sweep can archive
  nonpending checkpoint evidence with `archived_without_closeout` instead of
  pretending reviewed closeout occurred.
- Keep checkpoint backlog pressure inspectable before movement: runtime trace
  refs, session-memory archive refs, missing archive gaps, required actions,
  and next routes should be visible without moving evidence or mutating
  aoa-session-memory.
- Keep candidate intelligence below owner truth: checkpoint action facets,
  signatures, repetition clusters, and wrapper gaps may route review, but they
  do not accept skills, playbooks, techniques, evals, memo entries, SDK
  local checkpoint mechanics, or owner-local wrappers.
- Keep carrier intelligence as a separate ecosystem route layer: carrier
  candidates may name mechanic, tool, MCP, hook, script, daemon, service, or
  index pressure with owner scope and execution gates, but they do not install,
  register, execute, or accept those carriers.

## Next Work

- Tighten packet checks only after repeated checkpoint work proves stable
  fields and stop lines.
- Keep checkpoint output connected to the memory owner, proof owner, quest
  owner, and progression owner without claiming their verdicts.
- Preserve hook and handoff visibility without making the SDK a hidden workflow
  runner.
- Use lifecycle audit before close/archive cleanup so `current/` pressure is
  measured rather than guessed.
- Use reconcile/sweep dry-runs before applying no-closeout archive movement;
  generated checkpoint lifecycle indexes should route review, session-memory
  refs, candidates, commits, and graph-ready anchors without becoming memory
  or GraphRAG authority.
- Use `backlog-audit` before applying cleanup when `current/` contains many old
  scopes; route runtime trace gaps to session-memory freshness, sweep, import,
  or recovery checks before treating them as reconcile-ready.
- Use `candidate-intelligence` dry-runs before changing classifier rules;
  generated candidate indexes should route signatures, wrapper gaps, owner
  pressure, existing-fit status, and sample-audit targets without becoming
  memory, proof, or wrapper acceptance.
- Use `carrier-intelligence` dry-runs when the question is whether repeated
  action pressure suggests an ecosystem carrier such as a mechanic, tool, MCP
  access plane, hook, script, daemon, service, or generated index. Treat
  `sdk_local` as a private SDK scope, not the head pattern.

## When Time Comes

- Add a new checkpoint part when a repeated checkpoint route cannot fit capture,
  handoff runner, re-entry, or reviewed carry.
- Promote checkpoint output toward durable memory only through the memory owner
  and reviewed intake route.
- Add stronger closeout helpers only after checkpoint, questbook, release
  support, and owner handoff evidence repeat cleanly.
- Add stronger lifecycle transitions only when a repeated route proves the new
  state and its owner boundary; do not add states to explain a one-session tail.
- Add wrapper-specific automation only after repeated classifier samples have
  reviewed verdicts; do not convert a single action signature into an accepted
  aoa-* wrapper.
- Add carrier-specific implementation only after owner-scoped carrier samples
  have reviewed verdicts and the owning repo accepts install, registration, or
  execution posture.
- Add optional timers only as bounded wrappers around explicit sweep commands;
  do not add a hidden daemon that runs closeout, review, harvest, owner moves,
  or memory mutation.
- Add RAG/GraphRAG preparation only after raw/session evidence, generated
  indexes, and owner truth surfaces remain clearly separated; checkpoint
  backlog indexes can provide anchors, not retrieval authority.

## Out Of Scope

- Durable memory truth.
- Proof verdicts.
- Progression or quest acceptance.
- Automatic closeout, harvest, push, merge, or release logic.
- Hidden workflow execution.
- Mutating aoa-session-memory from checkpoint lifecycle routes.
- Treating runtime trace refs as proof that a session-memory archive exists.
- Promoting classifier output or generated candidate indexes into accepted
  wrappers without owner review.
- Treating generated carrier indexes as RAG, GraphRAG, install, registration,
  hook activation, tool execution, or owner-verdict authority.
