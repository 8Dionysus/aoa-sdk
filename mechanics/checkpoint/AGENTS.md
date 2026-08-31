# AGENTS.md

## Applies to

`mechanics/checkpoint/`.

## Role

Route the shared checkpoint mechanic for session-local note capture, git
boundary checks, review-note gates, promotion stop-lines, review-context
bundle assembly, reviewed evidence materialization, and reviewed closeout
context carry below owner truth without claiming capability execution. It also owns checkpoint lifecycle
audit and close/archive routing so stale `current/` scopes are visible and
movable without deleting evidence. It may attach read-only
aoa-session-memory archive refs to checkpoint closeout context, but it does not
promote memory claims. It may reconcile session-memory-backed checkpoint scopes
whose Codex session ended without reviewed closeout, but that route archives
local evidence only and does not create reviewed closeout. It may also derive
candidate-intelligence route evidence for repeated action signatures, wrapper
gaps, and owner pressure, but those classifier outputs stay unreviewed
navigation until an owner route accepts them.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/checkpoint/README.md`, `mechanics/checkpoint/ROADMAP.md`, `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/README.md`, `mechanics/checkpoint/parts/AGENTS.md`, `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md`, `mechanics/checkpoint/parts/reviewed-closeout-context-carry/README.md`, `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/AGENTS.md`, `docs/decisions/AOA-SDK-D-0068-reviewed-closeout-owner-handoff.md`, `src/aoa_sdk/checkpoints/`.

## Boundaries

- Stay on the control plane.
- Keep checkpoint notes session-local until reviewed promotion.
- Do not make checkpoint hints memory, proof, progression, or owner verdicts.
- Do not make reviewed closeout carry mint candidate, seed, object,
  continuity, component-refresh, or owner-acceptance truth.
- Do not close or archive checkpoint scopes with pending semantic review.
- Do not mutate aoa-session-memory when reading session-memory refs for
  checkpoint lifecycle or closeout evidence.
- Do not treat `archived_without_closeout` as `closed`.
- Do not treat candidate-intelligence signatures, repetition clusters, wrapper
  gaps, or generated indexes as accepted wrappers, memory, proof, or owner
  verdicts.
- Do not let hooks run closeout, harvest, push, merge, or release logic.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report whether capture, hook guard, review-note, promotion, review-context,
session-memory attachment, reviewed evidence materialization, or reviewed
closeout context carry, lifecycle audit, backlog audit, close/archive, or
no-closeout reconcile behavior changed. If candidate intelligence changed,
report whether the classifier stayed navigation-only and whether single-event
promotion remains blocked.
