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
  `AOA-SDK-D-0071` and the receipt-bound G5 owner switch in
  `AOA-SDK-D-0076`, which makes `aoa-sdk` the canonical routing producer
  while live runtime execution remains with the runtime owner
- the explicit non-publishing SDK G5 candidate builder and validator used to
  request stronger-owner artifact trust and runtime canary evidence without
  acquiring canonical producer authority
- the exact public SDK G5 release-candidate envelope, input lock, and
  deterministic archive used to establish release trust while normal runtime
  and every owner-switch authority flag remain denied
- the canonical G5 envelope, owner-switch receipt, exact public-release parity
  proof, compatibility-window start, and retained predecessor rollback posture
  while archival authority remains false
- the subsequent X2 archive closeout over immutable X1 evidence, which binds
  the separate exact operator approval, final predecessor release, preserved
  public GitHub archive state, and post-archive SDK-canonical runtime health
- the strict R2 route, plan, approval, lifecycle, event, evidence, and runtime
  adapter contract family, plus the C1 receipt-bound deterministic
  `AoASDK.control_plane.resolve()` and `.explain()` facade and the C2
  deterministic `AoASDK.control_plane.compile()` facade over an exact admitted
  `aoa-playbooks` contour, plus the C3 `AoASDK.runner` lifecycle client and
  deterministic no-execution reference adapter, plus the C4 explicit
  `abyss-stack` transport client and owner-exact profile loader; production
  runtime execution remains outside this repository

It does not own:

- live runtime execution, or skill, eval, memo, playbook, agent, progression,
  quest, checkpoint, service runtime, or frontend RPG semantics as source
  truth
- hidden heuristics that are not documented and testable

## Route

Start with this root card, then open the nearest nested AGENTS.md for every touched path. Read README.md, DESIGN.md, ROADMAP.md, owner docs, decisions, generated surfaces, or sibling-owner sources only when the touched path, semantic question, or requested operation makes them relevant. For executable checks, use the applicable nearest VALIDATION.md or the root human validation entrypoint VALIDATION.md; the root README remains a compact public route.

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

## Inspection and checkpoint route

When a task touches skills, checkpoint evidence, or additive surface detection, use the on-demand procedures in root VALIDATION.md. Skills inspection is passive only; it does not detect, rank,
dispatch, activate, or create skill-session state. Preserve session-local
evidence, owner-subordination, skipped_no_active_session, agent_review=pending,
and capability_execution_claimed=false; this card does not activate skills or
create live state.

## Landing route

Root AGENTS.md and .github/AGENTS.md still own branch, PR, CI, and merge semantics. When landing is explicitly requested, follow the exact six-step procedure in root VALIDATION.md; this local mechanical lane does not push, open PRs, wait on CI, merge, or alter sibling/live state.

## Validation route

Use root VALIDATION.md for repository inspection, focused checks, release-facing checks, the full owner gate, serial completeness and rollback, checkpoint review, and landing procedure. The canonical machine selector remains scripts/release_check.py; the owner claim/evidence manifest, accepted graph runner, and serial release_check.COMMANDS inventory remain authoritative.

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
