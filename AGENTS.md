# AGENTS.md

Root route card for `aoa-sdk`.

## Purpose

`aoa-sdk` is the typed Python SDK and control-plane helper layer for the AoA federation.
It consumes source-owned sibling surfaces and exposes local-first APIs for loading, validating, inspecting, materializing reviewed evidence, and handing off bounded federation objects.
It helps the federation stay legible without becoming the source of truth for sibling-layer meaning.

## Owner lane

This repository owns:

- typed SDK facades over consumed federation surfaces
- the SDK source-home topology under `sdk/`, including
  `sdk/source_home.manifest.json`, branch route cards, and SDK posture routes
- workspace discovery, topology resolution, compatibility checks, versioning posture, and CLI inspection surfaces
- the root `stats/` port for SDK-owned measurement questions and
  evidence-linked reference packets
- the canonical `skills/` home for admitted procedures over SDK-owned Titan
  helper contracts, without acquiring runtime, operator, memory, proof, or
  playbook authority
- the compact control-plane capsule at `generated/workspace_control_plane.min.json`
- the mechanics topology under `mechanics/`, including package route cards,
  source-family routes, future-pressure roadmaps, part-local artifact homes,
  `mechanics/topology.json`, package provenance cards, and part-local
  validation homes
- additive surface detection, passive skill-environment inspection, and
  reviewed checkpoint evidence handoff helpers that remain owner-subordinate
- the accepted staged routing-producer succession model in
  `AOA-SDK-D-0071`, while live producer authority remains with `aoa-routing`
  until the explicit G5 owner-switch receipt

It does not own:

- routing producer authority before G5, or skill, eval, memo, playbook, agent,
  progression, quest, checkpoint, service runtime, or frontend RPG semantics
  as source truth
- hidden heuristics that are not documented and testable

## Start here

1. `README.md`
2. `DESIGN.md` when repository shape, source-home placement, or mechanics
   topology changes
3. `DESIGN.AGENTS.md` when agent-facing guidance, local cards, validation
   posture, or closeout shape changes
4. `docs/boundaries.md`
5. `docs/workspace-layout.md`
6. `docs/versioning.md`
7. `ROADMAP.md`
8. `docs/decisions/README.md` when topology, owner split, route-law, workflow, or validator authority changes
9. `sdk/README.md` and `sdk/source_home.manifest.json` when SDK source-home
   posture, public-interface, facade-boundary, runtime-entry, or distribution
   topology changes
10. `stats/AGENTS.md`, `stats/README.md`, and `stats/port.manifest.json` when
    an SDK-owned statistical question or reference packet changes
11. `skills/AGENTS.md`, `skills/README.md`, and `skills/port.manifest.json`
    when an SDK-owned Titan helper procedure or owner exposure changes
12. `mechanics/README.md` and `mechanics/ROADMAP.md` when repeatable SDK
    operation topology, package routing, or mechanics future pressure changes
13. `.aoa/workspace.toml`
14. source files and tests you plan to touch


## AGENTS stack law

- Start with this root card, then follow the nearest nested `AGENTS.md` for every touched path.
- Root guidance owns repository identity, owner boundaries, route choice, and the shortest honest verification path.
- Nested guidance owns local contracts, local risk, exact files, and local checks.
- Authored source surfaces own meaning. Generated, exported, compact, derived, runtime, and adapter surfaces summarize, transport, or support meaning.
- Self-agency, recurrence, quest, progression, checkpoint, or growth language must stay bounded, reviewable, evidence-linked, and reversible.
- Report what changed, what was verified, what was not verified, and where the next agent should resume.

## Memory route

For control-plane recall, continuity, compaction recovery, comparison with past
work, or preserved lessons, start with `aoa-memo` and the workspace memory map.
Session grounding routes through `.aoa`; local candidate writing routes through
this repository's `memo/` port when that port exists; durable reviewed memory
lands through `aoa-memo`.

## Route and topology rules

- Stay on the control plane.
- Prefer explicit config and manifest-driven behavior over magical discovery.
- Keep source checkouts distinct from deployed runtime mirrors.
- Usual federation root is `/srv/AbyssOS`; `abyss-stack` source may live at `~/src/abyss-stack`, while `/srv/AbyssOS/abyss-stack` can be a runtime mirror.
- Consumed surfaces may be loaded, inspected, or handed off. Presence never
  becomes selection, activation, capability execution, or owner authority.

## Decision review

After structural, ownership, workflow, route-law, validator-authority,
public-contract, compatibility, or topology changes, check whether future
agents need a decision record to understand why the path was chosen. Use
`docs/decisions/AGENTS.md`, `docs/decisions/README.md`, and
`docs/decisions/TEMPLATE.md`.

Decision records explain rationale. They do not replace active SDK source,
boundary docs, generated companions, validators, or sibling-owner truth.

## Design review

Use `DESIGN.md` when a change alters repository shape, source-home placement,
source versus generated authority, compatibility posture, or `mechanics/`
package placement.

Use `DESIGN.AGENTS.md` when a change alters the root-to-local `AGENTS.md`
mesh, reading order, route-card shape, validation posture, closeout
expectations, or agent-facing design law.

Design surfaces describe form. They do not override active source code,
validators, decisions, nested route cards, or sibling-owner truth.

## Inspection And Checkpoint Loop

Use these compact anchors when a task touches skills, checkpoint evidence, or
additive surface detection:

```bash
aoa skills inspect /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json
aoa skills capability workflow.operations.checkpoint-closeout --root /srv/AbyssOS --json
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase ingress
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note
aoa checkpoint after-commit /srv/AbyssOS/aoa-sdk --commit-ref HEAD --root /srv/AbyssOS --json
aoa checkpoint review-note /srv/AbyssOS/aoa-sdk --commit-ref HEAD --auto
aoa checkpoint build-closeout-context /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json
aoa checkpoint materialize-closeout-handoff /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json
aoa checkpoint lifecycle-audit /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json
aoa checkpoint install-hook --repo aoa-sdk --hook all --root /srv/AbyssOS --json
aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv/AbyssOS --json
```

`aoa skills ...` is passive inspection only; it does not detect, rank,
dispatch, activate, or create skill-session state. Checkpoint notes and
materialized evidence stay session-local and owner-subordinate. A
`skipped_no_active_session` or `agent_review=pending` state is not final
review, and `capability_execution_claimed=false` must remain explicit through
materialization and A2A return.

## GitHub landing workflow

Root `AGENTS.md` owns the repository-wide branch, PR, CI, and merge route.
`.github/AGENTS.md` owns the GitHub-native files that support it.

When the user asks to commit, push, and merge in this repository, use this route:

1. Start from a branch based on the current `origin/main`. If the worktree is already dirty, inventory it first and carry forward only the intended diff.
2. Commit the intended change with a message that names the changed surface.
3. Push the branch and open a pull request that states changed surfaces, validation run, skipped checks, and remaining risk.
4. Wait for GitHub `Repo Validation` and any required GitHub checks. If a check fails, fix the branch and wait for the new result.
5. Merge through GitHub after green validation. Use squash unless repository settings report a different required method; report the method that landed.
6. Return to `main`, fast-forward from `origin/main`, and confirm the worktree is clean before closeout.

If GitHub status or merge permissions cannot be observed, stop the landing route and report the exact blocker instead of guessing.

## Verify

Minimum validation for code, topology, or reviewed-handoff changes:

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_sdk_source_home.py
python scripts/validate_local_stats_port.py
python scripts/validate_mechanics_topology.py
python scripts/build_source_topology_index.py --check
python scripts/validate_source_topology_index.py
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
For `sdk/` changes, also state which source-home branch changed and whether
implementation or mechanic payload moved.

## Retired root reference

The former preserved root-guidance dump is retired from active docs. Use this
root route card plus the nearest mechanic-owned docs for checkpoint, hook,
surface-detection, closeout, release, and compatibility work. If a rule from
the old dump still matters, restate it at the smallest active owner surface
instead of reintroducing a competing root reference.
