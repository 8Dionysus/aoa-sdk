# AGENTS.md

Root route card for `aoa-sdk`.

## Purpose

`aoa-sdk` is the typed Python SDK and control-plane helper layer for the AoA federation.
It consumes source-owned sibling surfaces and exposes local-first APIs for loading, validating, disclosing, activating, and handing off bounded federation objects.
It helps the federation stay legible without becoming the source of truth for sibling-layer meaning.

## Owner lane

This repository owns:

- typed SDK facades over consumed federation surfaces
- workspace discovery, topology resolution, compatibility checks, versioning posture, and CLI inspection surfaces
- the compact control-plane capsule at `generated/workspace_control_plane.min.json`
- additive surface detection and reviewed closeout handoff helpers that remain owner-subordinate

It does not own:

- routing, skill, eval, memo, playbook, agent, progression, quest, checkpoint, service runtime, or frontend RPG semantics as source truth
- hidden heuristics that are not documented and testable

## Start here

1. `README.md`
2. `docs/boundaries.md`
3. `docs/workspace-layout.md`
4. `docs/versioning.md`
5. `ROADMAP.md`
6. `.aoa/workspace.toml`
7. source files and tests you plan to touch
8. `docs/AGENTS_ROOT_REFERENCE.md` for preserved full root guidance, especially checkpoint-hook and closeout-loop details


## AGENTS stack law

- Start with this root card, then follow the nearest nested `AGENTS.md` for every touched path.
- Root guidance owns repository identity, owner boundaries, route choice, and the shortest honest verification path.
- Nested guidance owns local contracts, local risk, exact files, and local checks.
- Authored source surfaces own meaning. Generated, exported, compact, derived, runtime, and adapter surfaces summarize, transport, or support meaning.
- Self-agency, recurrence, quest, progression, checkpoint, or growth language must stay bounded, reviewable, evidence-linked, and reversible.
- Report what changed, what was verified, what was not verified, and where the next agent should resume.

## Route and topology rules

- Stay on the control plane.
- Prefer explicit config and manifest-driven behavior over magical discovery.
- Keep source checkouts distinct from deployed runtime mirrors.
- Usual federation root is `/srv/AbyssOS`; `abyss-stack` source may live at `~/src/abyss-stack`, while `/srv/AbyssOS/abyss-stack` can be a runtime mirror.
- Non-skill surfaces may be loaded, suggested, or handed off. They do not become executable-now activation authority.

## Surface Detection Loop

Use these compact anchors when a task touches checkpoint, handoff, or additive surface detection behavior:

```bash
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase ingress
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note
aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --mutation-surface code --root /srv/AbyssOS/aoa-sdk --json
aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "commit bounded patch" --mutation-surface code --root /srv/AbyssOS/aoa-sdk --json
aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "reviewable verify-green checkpoint" --mutation-surface code --checkpoint-kind verify_green
aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "refresh generated contracts" --mutation-surface code --no-auto-checkpoint --root /srv/AbyssOS/aoa-sdk --json
aoa checkpoint after-commit /srv/AbyssOS/aoa-sdk --commit-ref HEAD --root /srv/AbyssOS --json
aoa checkpoint review-note /srv/AbyssOS/aoa-sdk --commit-ref HEAD --auto
aoa checkpoint install-hook --repo aoa-sdk --hook all --root /srv/AbyssOS --json
aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv/AbyssOS --json
```

`aoa skills ...` remains skill-only. checkpoint notes stay lower-authority than harvest verdicts; `skipped_no_active_session` and `agent_review=pending` are session-local signals, not final review. A checkpoint note is a session-local ledger for harvest, progression, and quest hints through `checkpoint_capture.session_end_skill_targets`, `checkpoint_capture.progression_axis_signals`, and `checkpoint_capture.session_end_next_honest_move`. Keep `aoa-session-progression-lift` and `aoa-checkpoint-closeout-bridge` as reviewed-closeout helpers, remember that `manual-equivalent` never becomes `activated`, and routing shortlist hints stay advisory only.

## Verify

Minimum validation for code, topology, or reviewed-handoff changes:

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q
python -m ruff check .
aoa workspace inspect /srv/AbyssOS/aoa-sdk
aoa compatibility check /srv/AbyssOS/aoa-sdk
aoa compatibility check /srv/AbyssOS/aoa-sdk --repo aoa-skills --json
```

When release or CI-facing surfaces change, also run:

```bash
python -m mypy src
python -m build
python scripts/release_check.py
```

## Report

State which typed facade, discovery rule, compatibility surface, CLI behavior, checkpoint boundary, or handoff helper changed, whether anything moved closer to activation, and what validation ran.

## Full reference

`docs/AGENTS_ROOT_REFERENCE.md` preserves the former detailed root guidance, including the long surface-detection, checkpoint, hook, and closeout truth rules. Read it before editing those seams.
