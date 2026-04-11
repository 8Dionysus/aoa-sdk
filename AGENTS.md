# AGENTS.md

Guidance for coding agents and humans contributing to `aoa-sdk`.

## Purpose

`aoa-sdk` is the typed Python SDK for the AoA federation.
It consumes source-owned surfaces from sibling repositories and exposes a
local-first API layer for loading, validating, disclosing, activating, and
handing off bounded federation objects.

It is a control-plane helper layer.
It may make the federation easier to read and use as growth surfaces mature,
but it does not become the source of truth for progression doctrine, quest
meaning, role meaning, or runtime autonomy policy.

## Owns

This repository is the source of truth for:

- typed SDK facades over consumed federation surfaces
- the compact owner-owned control-plane capsule at `generated/workspace_control_plane.min.json`
- workspace discovery and topology resolution
- compatibility checks and versioning posture for consumed local surfaces
- bounded orchestration helpers that stay subordinate to source-owned meaning
- CLI inspection surfaces for workspace and compatibility views
- additive surface-detection and reviewed closeout-handoff helpers that stay subordinate to owner-layer truth

## Does not own

Do not treat this repository as the source of truth for:

- routing meaning in `aoa-routing`
- skill, eval, memo, playbook, agent, or progression meaning in sibling repositories
- service runtime behavior
- hidden workspace heuristics that are not documented and testable
- quest state, progression state, or checkpoint authority
- frontend theming or runtime RPG semantics

## Core rule

Stay on the control plane.

Prefer explicit, manifest-driven, reviewable behavior over magical discovery or
one-off path heuristics.
Preserve the distinction between source checkouts and deployed runtime mirrors.

## Read this first

Before making changes, read in this order:

1. `README.md`
2. `docs/boundaries.md`
3. `docs/workspace-layout.md`
4. `docs/versioning.md`
5. `.aoa/workspace.toml`
6. the source files and tests you plan to touch

Then branch by task:

- reviewed closeout handoff or session-growth targets: `docs/aoa-surface-detection-closeout-handoff.md`, `docs/session-growth-checkpoints.md`, and `docs/checkpoint-note-promotion.md`
- additive surface detection: `docs/aoa-surface-detection-first-wave.md`, `docs/aoa-surface-detection-second-wave.md`, and `docs/aoa-surface-detection-heuristics.md`
- RPG / progression readers: `docs/RPG_SDK_ADDENDUM.md` and `docs/RPG_SURFACE_PATHS.md`
- release, CI, or compatibility posture: `docs/RELEASE_CI_POSTURE.md` and `docs/ecosystem-impact.md`
- federation release audit or publish work: `docs/RELEASING.md` and `scripts/release_check.py`

If a deeper directory defines its own `AGENTS.md`, follow the nearest one.

## Workspace topology

- The usual federation root is `/srv`, where `aoa-sdk` and sibling AoA repositories live as peer directories.
- `abyss-stack` is the important exception: the source checkout lives at `~/src/abyss-stack`.
- `/srv/abyss-stack` is a deployed runtime mirror, not the preferred source checkout.
- If both paths exist, prefer editing `~/src/abyss-stack`.
- `src/aoa_sdk/workspace/discovery.py`, `.aoa/workspace.toml`, and `docs/workspace-layout.md` must stay aligned.

## Growth posture

`aoa-sdk` may expose typed readers and helpers for reviewed closeout handoff,
session-growth notes, progression overlays, and adjunct RPG reflection.

Those helpers must remain:

- owner-subordinate
- reviewable
- explicit about truth labels
- explicit about whether a surface is only loaded, only suggested, manually equivalent, or activated

The SDK may help the federation stay legible as it grows.
It must not silently convert growth vocabulary into live policy.

## Primary objects

The most important objects in this repository are:

- workspace discovery and topology code under `src/aoa_sdk/workspace/`
- typed surface facades under `src/aoa_sdk/`
- `.aoa/workspace.toml`
- `generated/workspace_control_plane.min.json`
- topology, boundary, and versioning docs under `docs/`
- additive surface-detection docs and heuristics under `docs/aoa-surface-detection-*.md` and `src/aoa_sdk/surfaces/`
- tests that prove discovery, compatibility, typed read paths, and reviewed handoff shape

## Hard NO

Do not:

- pull source-owned meaning into the SDK
- replace explicit config with hidden path guessing
- blur source checkouts with runtime mirrors
- turn `aoa-sdk` into a service runtime or monolith
- change topology behavior without updating docs and tests in the same change
- blur `activated` and `manual-equivalent`, or quietly make non-skill surfaces executable-now
- let helper methods mutate quest state, progression state, or checkpoint state
- auto-promote reviewed closeout handoffs into live activation or routing policy
- flatten multi-axis progression into one score or one magic readiness flag
- let convenience helpers hide source refs, truth labels, or owner boundaries

## Surface Detection Loop

Keep `aoa skills enter` and `aoa skills guard` as the primary session-start and
pre-mutation paths.
They stay skill-only.
By default they may also append one local checkpoint note when checkpoint-phase
surface detection finds a real growth signal.
Explicit `commit` and `verify-green` intents on a real mutation surface also
count as growth seams for that local note, even when recurring-route heuristics
stay quiet.
Treat that note as the session-local ledger for harvest, progression, and
upgrade candidates until reviewed closeout; it should also carry provisional
multi-axis progression evidence for `aoa-session-progression-lift`.
Do not move candidates or stats mid-session just
because the note became reviewable.
Expect `aoa skills enter` and `aoa skills guard` to expose that reviewed-closeout
plan directly in `checkpoint_capture.session_end_skill_targets` and
`checkpoint_capture.session_end_next_honest_move`, with
`checkpoint_capture.progression_axis_signals` showing the provisional axis
movement that should be lifted only at reviewed closeout.
Use `aoa-checkpoint-closeout-bridge` for the explicit reviewed-closeout chain:
build one `closeout-context.json` bundle, reread the reviewed artifact, and
then run donor harvest, progression lift, and quest harvest in that order.
Do not turn `aoa closeout run` into the hidden runtime for that chain.
Use `--no-auto-checkpoint` when you need the skill lane to stay read-only apart
from its persisted report, and use `--checkpoint-kind` when one explicit
checkpoint event matters.
When a repo has the installed `aoa-sdk` `post-commit` hook, a plain
`git commit` may also run `aoa checkpoint after-commit` automatically.
That path is active-session-only: if the resolved thread-scoped or default
runtime session file does not already exist, it must exit as
`skipped_no_active_session` and must not create a new session just to emit
checkpoint noise.
That hook path may dispatch checkpoint-phase skills, run additive checkpoint
surface detection, and append one reviewable local note, but it must never run
closeout, promotion, harvest, push, or release logic.
The hook defaults to `--kind auto`: ordinary commits stay `commit/code`, but an
explicit `AOA_CHECKPOINT_KIND=owner_followthrough`, owner-follow-through commit
text, or an already closed/promoted active checkpoint note records
`owner_followthrough/public-share` follow-through without rotating or reopening
the closed note.
The hook-created checkpoint starts as `agent_review=pending`; after every
successful commit, the Codex agent must apply the checkpoint skill protocol and
write a semantic `aoa checkpoint review-note` entry before treating the commit
as fully handled.
That review note is where the agent records what changed, why it matters, where
the candidate belongs, stats hints, mechanic hints, closeout questions, and
evidence refs. Scripts may preserve the checkpoint boundary, but scripts do not
replace the agent's semantic review.
Do not treat that local side effect as a change to skill ownership semantics.

When the task shows route drift, owner-layer ambiguity, proof need, recall
need, role posture questions, or recurring-scenario signals, run one additive
surface pass:

```bash
aoa surfaces detect /srv/aoa-sdk --phase ingress --intent-text "verify recurring handoff proof" --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase pre-mutation --intent-text "prove and recall a recurring route" --mutation-surface code --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --mutation-surface code --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "commit bounded patch" --mutation-surface code --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "reviewable verify-green checkpoint" --mutation-surface code --checkpoint-kind verify_green --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "refresh generated contracts" --mutation-surface code --no-auto-checkpoint --root /srv/aoa-sdk --json
aoa checkpoint after-commit /srv/aoa-sdk --commit-ref HEAD --root /srv --json
aoa checkpoint after-commit /srv/aoa-sdk --commit-ref HEAD --kind owner_followthrough --root /srv --json
aoa checkpoint review-note /srv/aoa-sdk --commit-ref HEAD --summary "agent-reviewed checkpoint notes for this commit" --finding "what changed and why it matters" --candidate-note "candidate, owner, and where it should be revisited" --stats-hint "stats to refresh only after reviewed closeout" --mechanic-hint "workflow mechanism to retain" --closeout-question "what to verify when rereading the full session" --applied-skill aoa-change-protocol --root /srv --json
aoa checkpoint install-hook --repo aoa-sdk --root /srv --json
aoa checkpoint hook-status --repo aoa-sdk --root /srv --json
```

Use `aoa surfaces handoff` only after review:

```bash
aoa surfaces handoff /srv/aoa-sdk/.aoa/surface-detection/aoa-sdk.closeout.latest.json --session-ref session:2026-04-07-surface-first-wave --reviewed --root /srv/aoa-sdk --json
```

Truth rules for this loop:

- `aoa-sdk` may detect and hand off, but owner repositories keep meaning
- `aoa skills ...` remains skill-only
- checkpoint notes stay lower-authority than harvest verdicts and core receipts
- `manual-equivalent` never becomes `activated`
- non-skill surfaces never become executable-now in wave one
- routing shortlist hints stay advisory only
- reviewed closeout handoff never auto-runs from `aoa closeout run`
- surviving items keep their existing truth labels through handoff
- `aoa-stats.surface_detection_summary.min` stays descriptive only

## Contribution doctrine

Use this flow: `PLAN -> DIFF -> VERIFY -> REPORT`

### PLAN

State:

- which typed facade, discovery rule, compatibility surface, or reviewed handoff helper is changing
- which sibling repositories are affected
- whether workspace topology or CLI behavior changes
- what boundary, activation, or compatibility risk exists

### DIFF

Keep the change focused.
Prefer config and manifest-driven behavior over special-case code.
Preserve local-first ergonomics without stealing ownership from the source repos.

### VERIFY

Minimum validation for code, topology, or reviewed-handoff changes:

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q
python -m ruff check .
aoa workspace inspect /srv/aoa-sdk
aoa compatibility check /srv/aoa-sdk
aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json
```

When release or CI-facing surfaces change, also run:

```bash
python -m mypy src
python -m build
python scripts/release_check.py
```

Confirm that owner meaning, truth labels, and checkpoint boundaries remain
legible in the changed helpers.

### REPORT

Summarize:

- what changed
- which typed surfaces, topology rules, or handoff contracts changed
- whether compatibility or CLI behavior changed
- whether any helper posture moved closer to activation or remained reviewed-only
- what validation you actually ran
- any remaining follow-up work

## Validation

Do not claim checks you did not run.
When changing topology behavior, update tests and docs in the same change.
