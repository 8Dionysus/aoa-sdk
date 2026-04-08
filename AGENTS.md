# AGENTS.md

Guidance for coding agents and humans contributing to `aoa-sdk`.

## Purpose

`aoa-sdk` is the typed Python SDK for the AoA federation. It consumes source-owned surfaces from sibling repositories and exposes a local-first API layer for loading, validating, disclosing, activating, and handing off bounded federation objects.

## Owns

This repository is the source of truth for:

- typed SDK facades over consumed federation surfaces
- workspace discovery and topology resolution
- compatibility checks and versioning posture for consumed local surfaces
- bounded orchestration helpers that stay subordinate to source-owned meaning
- CLI inspection surfaces for workspace and compatibility views

## Does not own

Do not treat this repository as the source of truth for:

- routing meaning in `aoa-routing`
- skill, eval, memo, playbook, or agent meaning in sibling repositories
- service runtime behavior
- hidden workspace heuristics that are not documented and testable

## Core rule

Stay on the control plane.

Prefer explicit, manifest-driven, reviewable behavior over magical discovery or one-off path heuristics. Preserve the distinction between source checkouts and deployed runtime mirrors.

## Read this first

Before making changes, read in this order:

1. `README.md`
2. `docs/boundaries.md`
3. `docs/workspace-layout.md`
4. `docs/versioning.md`
5. `.aoa/workspace.toml`
6. the source files and tests you plan to touch

If a deeper directory defines its own `AGENTS.md`, follow the nearest one.

## Workspace topology

- The usual federation root is `/srv`, where `aoa-sdk` and sibling AoA repositories live as peer directories.
- `abyss-stack` is the important exception: the source checkout lives at `~/src/abyss-stack`.
- `/srv/abyss-stack` is a deployed runtime mirror, not the preferred source checkout.
- If both paths exist, prefer editing `~/src/abyss-stack`.
- `src/aoa_sdk/workspace/discovery.py`, `.aoa/workspace.toml`, and `docs/workspace-layout.md` must stay aligned.

## Primary objects

The most important objects in this repository are:

- workspace discovery and topology code under `src/aoa_sdk/workspace/`
- typed surface facades under `src/aoa_sdk/`
- `.aoa/workspace.toml`
- topology, boundary, and versioning docs under `docs/`
- additive surface-detection docs and heuristics under `docs/aoa-surface-detection-*.md` and `src/aoa_sdk/surfaces/`
- tests that prove discovery, compatibility, and typed read paths

## Hard NO

Do not:

- pull source-owned meaning into the SDK
- replace explicit config with hidden path guessing
- blur source checkouts with runtime mirrors
- turn `aoa-sdk` into a service runtime or monolith
- change topology behavior without updating docs and tests in the same change
- blur `activated` and `manual-equivalent`, or quietly make non-skill surfaces executable-now

## Surface Detection Loop

Keep `aoa skills enter` and `aoa skills guard` as the primary session-start and
pre-mutation paths. They stay skill-only.

When the task shows route drift, owner-layer ambiguity, proof need, recall
need, role posture questions, or recurring-scenario signals, run one additive
surface pass:

```bash
aoa surfaces detect /srv/aoa-sdk --phase ingress --intent-text "verify recurring handoff proof" --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase pre-mutation --intent-text "prove and recall a recurring route" --mutation-surface code --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
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
- `aoa-stats.surface_detection_summary.min` stays descriptive only

## Contribution doctrine

Use this flow: `PLAN -> DIFF -> VERIFY -> REPORT`

### PLAN

State:

- which typed facade, discovery rule, or compatibility surface is changing
- which sibling repositories are affected
- whether workspace topology or CLI behavior changes
- what boundary or compatibility risk exists

### DIFF

Keep the change focused. Prefer config and manifest-driven behavior over special-case code. Preserve local-first ergonomics without stealing ownership from the source repos.

### VERIFY

Minimum validation for code or topology changes:

```bash
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
```

### REPORT

Summarize:

- what changed
- which typed surfaces or topology rules changed
- whether compatibility or CLI behavior changed
- what validation you actually ran
- any remaining follow-up work

## Validation

Do not claim checks you did not run.

When changing topology behavior, update tests and docs in the same change.
