# aoa-sdk

Typed Python SDK for the AoA federation.

`aoa-sdk` is the local-first typed consumer and control-plane helper layer for source-owned AoA surfaces. It loads generated contracts from sibling repositories and exposes stable Python APIs for routing, skill discovery and activation, phase-aware artifact reads, compatibility checks, governed-run inspection, and other bounded control-plane helpers without taking ownership away from the repositories that define meaning.

This repository was seeded from the `Dionysus` starter artifacts on 2026-03-31. It is now the live development home for the SDK itself.

> Current release: `v0.2.3`. See [CHANGELOG](CHANGELOG.md) for release notes.

## Start here

Use the shortest route by need:

- ownership and scope: `docs/boundaries.md`
- compact control-plane capsule: `generated/workspace_control_plane.min.json`
- workspace topology and override rules: `docs/workspace-layout.md` and `.aoa/workspace.toml`
- compatibility posture: `docs/versioning.md`
- recurrence manifest compatibility gate: `docs/RECURRENCE_HARDENING_COMPATIBILITY.md`, `aoa recur manifest-scan --root /srv --json`, and `python scripts/validate_recurrence_manifests.py --workspace-root /srv`
- recurrence graph closure and snapshots: `docs/RECURRENCE_GRAPH_CLOSURE_AND_SNAPSHOT.md`, `aoa recur graph snapshot --root /srv --json`, and `aoa recur graph closure --root /srv --component component:<owner>:<name> --json`
- recurrence live observation producers: `docs/RECURRENCE_LIVE_OBSERVATION_PRODUCERS.md`, `aoa recur live producers --root /srv --json`, and `python scripts/collect_live_recurrence_observations.py --workspace-root /srv --json`
- recurrence review decision closure: `docs/RECURRENCE_REVIEW_DECISION_CLOSURE.md`, `aoa recur review decision-template --root /srv`, and `python scripts/review_decision_closure.py --workspace-root /srv template`
- recurrence downstream projections: `docs/RECURRENCE_DOWNSTREAM_PROJECTIONS.md`, `aoa recur project build --root /srv --json`, and `python scripts/build_downstream_recurrence_projections.py --workspace-root /srv --json`
- recurrence eval-suite handoff: `docs/RECURRENCE_EVAL_SUITE_HANDOFF.md` and `aoa-evals/bundles/aoa-recurrence-control-plane-integrity/`
- current direction and hardening lanes: `ROADMAP.md`
- release protocol and bounded publication path: `docs/RELEASING.md`
- release, support, and CI posture: `docs/RELEASE_CI_POSTURE.md`
- reviewed session closeout orchestration: `docs/session-closeout.md`
- reviewed closeout followthrough map toward owner-status surfaces: `docs/closeout-followthrough-map.md`, `schemas/closeout_owner_followthrough_map.schema.json`, and `examples/closeout_owner_followthrough_map.example.json`
- component drift hints and reviewed refresh decisions that stay weaker than owner refresh law: `docs/COMPONENT_DRIFT_HINTS.md`, `schemas/component_drift_hint_set.schema.json`, `examples/component_drift_hints.example.json`, `schemas/component_refresh_followthrough_decision_set.schema.json`, and `examples/component_refresh_followthrough_decision.example.json`
- reviewed continuity hints after closeout reread: `docs/SELF_AGENCY_CONTINUITY_CARRY.md`, `schemas/closeout_continuity_window.schema.json`, and `examples/closeout_continuity_window.example.json`
- reviewed next-kernel decision after closeout reread: `docs/SESSION_GROWTH_KERNEL_SIGNAL_RULES.md`, `schemas/closeout_followthrough_decision.schema.json`, and `examples/closeout_followthrough_decision.example.json`
- additive surface detection and reviewed owner-layer handoff: `docs/aoa-surface-detection-first-wave.md`, `docs/aoa-surface-detection-second-wave.md`, `docs/aoa-surface-detection-heuristics.md`, and `docs/aoa-surface-detection-closeout-handoff.md`
- checkpoint-aware session-growth note capture and promotion: `docs/session-growth-checkpoints.md` and `docs/checkpoint-note-promotion.md`
- antifragility control-plane and closeout contracts: `docs/antifragility-control-plane.md`, `docs/antifragility-closeout-seam.md`, `tests/fixtures/antifragility/stress_dispatch_input.example.json`, `tests/fixtures/antifragility/stress_dispatch_result.example.json`, and `tests/fixtures/antifragility/stress_closeout_manifest.example.json`
- RPG typed consumer slice: `docs/RPG_SDK_ADDENDUM.md`, `docs/RPG_SURFACE_PATHS.md`, and `src/aoa_sdk/rpg/`
- Titan runtime harness, operator console, app-server bridge, identity ledger, and Memory Loom control-plane surfaces: `docs/TITAN_RUNTIME_HARNESS.md`, `docs/TITAN_OPERATOR_CONSOLE.md`, `docs/TITAN_APPSERVER_BRIDGE.md`, `docs/TITAN_IDENTITY_LEDGER.md`, `docs/TITAN_MEMORY_LOOM.md`, `src/aoa_sdk/titans/`, and `scripts/titanctl.py`
- federation effects and obligations: `docs/ecosystem-impact.md`
- original seed blueprint and historical design context: `docs/blueprint.md`
- Wave 1 AoA experience capture/pipeline helper seam: `docs/AGON_WAVE1_EXPERIENCE_CAPTURE_PIPELINE.md`, `schemas/agon-experience-capture-pipeline-helper.schema.json`, and `examples/agon_experience_capture_pipeline_helper.example.json`
- local agent instructions: `AGENTS.md`

## Route by need

- compact control-plane capsule for low-context routing: `generated/workspace_control_plane.min.json`
- current direction and control-plane hardening: `ROADMAP.md`
- machine-readable workspace and discovery alignment: `.aoa/workspace.toml`, `src/aoa_sdk/workspace/discovery.py`, and `docs/workspace-layout.md`
- project-level Codex workspace orientation via MCP: `docs/codex-workspace-mcp.md`, `src/aoa_sdk/codex/workspace_mcp.py`, and `scripts/aoa_workspace_mcp_server.py`
- portable sibling-workspace bootstrap for non-`/srv` installs: `aoa workspace bootstrap`, `src/aoa_sdk/workspace/bootstrap.py`, and `8Dionysus/docs/WORKSPACE_INSTALL.md`
- Codex-plane portability boundary when the live root changes: `docs/CODEX_PLANE_PORTABILITY.md` and `8Dionysus/docs/CODEX_PLANE_REGENERATION.md`
- live Codex-plane rollout status at the current workspace root: `docs/CODEX_PLANE_DEPLOY_STATUS.md`, `docs/CODEX_DEPLOY_OPERATION_BOUNDARY_NOTE.md`, `docs/codex_rollout_campaign_refs.md`, `schemas/codex_plane_deploy_status_snapshot_v1.json`, `examples/codex_plane_deploy_status_snapshot.example.json`, and `src/aoa_sdk/codex/registry.py`
- source ownership and federation effects: `docs/boundaries.md` and `docs/ecosystem-impact.md`
- compatibility rules and local checks: `docs/versioning.md`, `scripts/sibling_canary_matrix.json`, `scripts/run_sibling_canary.py`, `.github/workflows/latest-sibling-canary.yml`, `aoa compatibility check /srv/aoa-sdk`, and `aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json`
- recurrence manifest compatibility: `docs/RECURRENCE_CONTROL_PLANE.md`, `docs/RECURRENCE_HARDENING_COMPATIBILITY.md`, `schemas/manifest_scan_report.schema.json`, `src/aoa_sdk/recurrence/compat.py`, `aoa recur manifest-scan --root /srv --json`, and `python scripts/validate_recurrence_manifests.py --workspace-root /srv`
- recurrence graph inspection: `docs/RECURRENCE_GRAPH_CLOSURE_AND_SNAPSHOT.md`, `schemas/graph_snapshot.schema.json`, `schemas/graph_closure_report.schema.json`, `schemas/graph_delta_report.schema.json`, `src/aoa_sdk/recurrence/graph.py`, `aoa recur graph snapshot --root /srv --json`, `aoa recur graph closure --root /srv --component component:<owner>:<name> --json`, and `python scripts/build_recurrence_graph_snapshot.py --workspace-root /srv --json`
- recurrence live observations: `docs/RECURRENCE_LIVE_OBSERVATION_PRODUCERS.md`, `schemas/live_observation_run.schema.json`, `src/aoa_sdk/recurrence/live_observations.py`, `aoa recur live observe --root /srv --json`, and `python scripts/collect_live_recurrence_observations.py --workspace-root /srv --json`
- recurrence review decision closure: `docs/RECURRENCE_REVIEW_DECISION_CLOSURE.md`, `schemas/owner_review_decision.schema.json`, `schemas/review_decision_close_report.schema.json`, `src/aoa_sdk/recurrence/decisions.py`, `aoa recur review decision-template --root /srv`, `aoa recur review close --root /srv`, and `python scripts/review_decision_closure.py --workspace-root /srv template`
- recurrence downstream projections: `docs/RECURRENCE_DOWNSTREAM_PROJECTIONS.md`, `schemas/downstream-projection-bundle.schema.json`, `schemas/downstream-projection-guard-report.schema.json`, `src/aoa_sdk/recurrence/projections.py`, `aoa recur project routing|stats|kag|build --root /srv`, and `python scripts/build_downstream_recurrence_projections.py --workspace-root /srv --json`
- recurrence eval-suite handoff to the proof layer: `docs/RECURRENCE_EVAL_SUITE_HANDOFF.md`, with proof ownership remaining in `aoa-evals`
- public support, release scope, and CI tiers: `docs/RELEASE_CI_POSTURE.md`
- bounded federation release audit and publish helper: `docs/RELEASING.md`, `aoa release audit /srv --phase preflight --all --json`, and `aoa release publish /srv --repo aoa-sdk --dry-run --json`
- typed facade and downstream-consumer entrypoints: `src/aoa_sdk/`, `tests/`, and the example under `Current slice`
- Titan runtime and bridge helpers that stay subordinate to role, memory, proof, and owner-repo truth: `src/aoa_sdk/titans/`, `scripts/titanctl.py`, `scripts/titan_console.py`, `scripts/titan_appserver_bridge.py`, `scripts/titan_memory_loom.py`, `scripts/titan_lineage.py`, and `tests/test_titan_*.py`
- local validation and workspace inspection: `python scripts/build_workspace_control_plane.py --check`, `python scripts/validate_workspace_control_plane.py`, `aoa workspace inspect /srv/aoa-sdk`, `aoa compatibility check /srv/aoa-sdk`, `python -m pytest -q`, and `python -m ruff check .`
- reviewed session closeout queue and reports: `docs/session-closeout.md`, `aoa closeout run`, and `aoa closeout process-inbox`
- reviewed closeout followthrough hints that stay advisory: `docs/closeout-followthrough-map.md`, `examples/closeout_owner_followthrough_map.example.json`, and `closeout-context.json` under `.aoa/session-growth/current/.../`
- component-refresh control-plane carry that stays hint-only or reviewed-only: `docs/COMPONENT_DRIFT_HINTS.md`, `examples/component_drift_hints.example.json`, `examples/component_refresh_followthrough_decision.example.json`, and `closeout-context.json` under `.aoa/session-growth/current/.../`
- hint-only self-agency continuity carry after reviewed closeout: `docs/SELF_AGENCY_CONTINUITY_CARRY.md`, `examples/closeout_continuity_window.example.json`, and `closeout-context.json` under `.aoa/session-growth/current/.../`
- deterministic next-kernel hints after reviewed closeout: `docs/SESSION_GROWTH_KERNEL_SIGNAL_RULES.md`, `examples/closeout_followthrough_decision.example.json`, and `closeout-context.json` under `.aoa/session-growth/current/.../`
- additive owner-layer surface detection without changing `aoa skills ...` meaning: `docs/aoa-surface-detection-first-wave.md`, `aoa surfaces detect`, and `src/aoa_sdk/surfaces/`
- checkpoint-aware local session-growth note capture and promotion: `docs/session-growth-checkpoints.md`, `docs/checkpoint-note-promotion.md`, `aoa checkpoint mark/append/after-commit/review-note/status/promote`, `aoa checkpoint install-hook`, `aoa checkpoint hook-status`, the auto checkpoint bridge on `aoa skills guard`, and the explicit `aoa skills enter --checkpoint-kind` / `--append-note` overrides
- explicit checkpoint-to-closeout bridge orchestration: `docs/session-growth-checkpoints.md`, `docs/session-closeout.md`, `aoa checkpoint build-closeout-context`, and `aoa checkpoint execute-closeout-chain`
- second-wave shortlist, receipt-context, and observability seams that stay advisory: `docs/aoa-surface-detection-second-wave.md`, `sdk.routing.owner_layer_shortlist()`, and `sdk.stats.surface_detection()`
- stats-driven re-grounding policy: `docs/STATS_REGROUNDING_POLICY.md`, `sdk.stats.source_coverage()`, `sdk.stats.surface_profile()`, `sdk.stats.regrounding_signal()`, and `sdk.routing.stats_regrounding_hints()`
- antifragility stress-context doctrine and fixtures that stay narrowing-only: `docs/antifragility-control-plane.md`, `docs/antifragility-closeout-seam.md`, `tests/fixtures/antifragility/stress_dispatch_input.example.json`, `tests/fixtures/antifragility/stress_dispatch_result.example.json`, and `tests/fixtures/antifragility/stress_closeout_manifest.example.json`
- via negativa pruning checklist: `docs/VIA_NEGATIVA_CHECKLIST.md`
- deterministic first-wave heuristics for proof, recall, recurring routes, role posture, and repeated practice: `docs/aoa-surface-detection-heuristics.md` and `src/aoa_sdk/surfaces/heuristics.py`
- reviewed-only closeout handoff for surviving surface notes: `docs/aoa-surface-detection-closeout-handoff.md`, `aoa surfaces handoff`, and `docs/session-closeout.md`
- reviewed session auto-closeout inbox: `docs/session-closeout.md`, `aoa closeout enqueue-current`, `aoa closeout status`, and `scripts/install_closeout_units.py`
- reviewed session manifest assembly: `docs/session-closeout.md` and `aoa closeout build-manifest`
- reviewed session request assembly from receipt bundles or audit-only reviewed artifacts: `docs/session-closeout.md` and `aoa closeout submit-reviewed`
- kernel-aware next-step brief after reviewed closeout: `docs/session-closeout.md`, `aoa closeout run`, and `aoa closeout process-inbox`
- persistent owner follow-through handoffs after harvest or quest promotion: `docs/session-closeout.md`, `.aoa/closeout/handoffs/`, `aoa closeout run`, and `aoa closeout process-inbox`
- workspace session ingress and pre-mutation guard wrappers: `aoa skills enter`, `aoa skills guard`, and `src/aoa_sdk/cli/main.py`
- router recommendation versus host skill-availability gap: `docs/skill-runtime-recommendation-gap.md`, `aoa skills enter`, `aoa skills guard`, and `src/aoa_sdk/skills/detector.py`
- first implementation spec for the recommendation-availability gap: `docs/skill-runtime-recommendation-gap-fix-spec.md`, `src/aoa_sdk/models.py`, `src/aoa_sdk/skills/detector.py`, and `src/aoa_sdk/cli/main.py`
- project foundation structure and layer order: `sdk.skills.project_foundation()` and the `aoa-skills` generated foundation surface
- project-core outer-ring structure and readiness: `sdk.skills.project_core_outer_ring()`, `sdk.skills.project_core_outer_ring_readiness()`, and the `aoa-skills` generated project-core ring surfaces
- project risk guard ring structure and governance: `sdk.skills.project_risk_guard_ring()`, `sdk.skills.project_risk_guard_ring_governance()`, and the `aoa-skills` generated risk-ring surfaces
- phase-aware skill detection and safe auto-dispatch: `aoa skills detect`, `aoa skills dispatch`, and `src/aoa_sdk/skills/detector.py` with `ingress`, `pre-mutation`, `checkpoint`, and `closeout` phases

## What `aoa-sdk` owns

This repository is the source of truth for:

- typed loaders and facades over source-owned federation surfaces
- workspace discovery and topology resolution
- compatibility checks across consumed local surfaces
- bounded activation, disclosure, and orchestration helpers
- reviewed-session closeout helpers that publish owner-local receipts and refresh live stats
- reviewed-session inbox automation that stays subordinate to reviewed manifests and owner-owned publishers
- canonical manifest assembly from reviewed artifacts and receipt paths, with optional audit-only reviewed closeout when no owner-local receipts exist yet
- canonical request assembly from reviewed artifacts plus receipt bundles before manifest/enqueue
- separate closeout routing for skill-detail receipts and generic project-core kernel skill-application receipts
- kernel-aware next-step brief generation based on `aoa-skills.project_core_skill_kernel.min` and refreshed `aoa-stats.core_skill_application_summary.min`
- typed readability for the baseline project foundation from `aoa-skills.project_foundation_profile.min`
- typed readability for the static project-core engineering outer ring from `aoa-skills.project_core_outer_ring.min` and `aoa-skills.project_core_outer_ring_readiness.min`
- typed readability for the static project risk guard ring from `aoa-skills.project_risk_guard_ring.min` and `aoa-skills.project_risk_guard_ring_governance.min`
- phase-aware skill detection and dispatch that only auto-activates `explicit-preferred` foundation skills and keeps `explicit-only` skills in visible confirmation lanes
- persisted workspace-level ingress and guard reports under `aoa-sdk/.aoa/skill-dispatch/` so outer wrappers and root-level agents can reuse one stable session-start surface
- default skill runtime session storage under `aoa-sdk/.aoa/skill-runtime-sessions/<codex-thread>.json` when `CODEX_THREAD_ID` is available, otherwise under `aoa-sdk/.aoa/skill-runtime-session.json`
- additive first-wave and second-wave surface detection under `aoa-sdk/.aoa/surface-detection/` that keeps `aoa skills ...` skill-only while surfacing eval, memo, playbook, agent, and technique candidates as non-executable hints or reviewed handoffs
- local checkpoint-note capture under `aoa-sdk/.aoa/session-growth/current/` that keeps mid-session growth work below harvest-verdict authority until reviewed promotion, carries harvest, progression, and upgrade candidates through the session, records provisional progression-axis movement, rotates `current` by active checkpoint session rather than day-only naming, and leaves candidate movement plus stats refresh to reviewed closeout
- active-session-only post-commit checkpoint capture for plain `git commit`, writing one runtime-scoped `post-commit-report.json` when a session exists, one structured auto-observation inside the checkpoint note, and one fallback status artifact under `aoa-sdk/.aoa/session-growth/post-commit-status/` when capture skips or fails before note state is available
- with an active runtime session, legacy unscoped `current/<repo>` checkpoint ledgers are quarantine-only migration evidence and do not auto-attach to the live session
- agent-authored post-commit checkpoint reviews through `aoa checkpoint review-note`; `--auto` now lets the Codex agent promote the matching `auto_observation` into a full semantic review without retyping summary/findings by hand, while manual flags still remain available for richer followthrough
- when a checkpoint note still has pending agent reviews, the session-growth next-step guidance now points to `aoa checkpoint review-note --auto` first instead of prematurely steering into reviewed closeout
- `aoa checkpoint build-closeout-context` and `aoa checkpoint execute-closeout-chain` now fail closed while any aggregated checkpoint note in the active runtime session still has `agent_review=pending`
- once those pending reviews are cleared, `closeout-context.json` now carries the aggregated semantic checkpoint-review material itself, including review refs, findings, closeout questions, mechanic hints, and inherited auto-observation provenance
- the mechanical closeout outputs produced through the bridge now carry that same checkpoint-review bundle forward into donor, progression, and quest artifacts so downstream rereads do not have to reconstruct it from the note by hand
- once checkpoint bridge closeout emits surviving owner follow-through, it now also writes one persistent `.aoa/closeout/handoffs/*.owner-handoff.json` bundle rooted in the reviewed `closeout-context.json`, so the next owner authoring move does not disappear back into runtime-local bridge artifacts
- a checkpoint note now flips to `review_status=reviewed` once its agent review is actually present and no checkpoint review remains pending
- `aoa checkpoint promote` now fails closed on pending checkpoint reviews instead of allowing promotion to jump ahead of the semantic review step
- `aoa skills enter` and `aoa skills guard` now expose the pending reviewed-closeout skill-family plan through `checkpoint_capture.session_end_skill_targets`, `checkpoint_capture.progression_axis_signals`, and `checkpoint_capture.session_end_next_honest_move`
- reviewed closeout can now raise `aoa-session-progression-lift` from the checkpoint ledger before `aoa-quest-harvest`, so multi-axis progression stays evidence-backed and end-of-session only
- reviewed closeout can now build one `closeout-context.json` bundle and execute the explicit `aoa-checkpoint-closeout-bridge` chain without turning `aoa closeout run` into a hidden skill runner
- reviewed closeout may now also publish one hint-only continuity window so a
  later bounded reanchor can stay inspectable without turning the SDK into a
  self-agency owner
- reviewed closeout may also carry component drift hints and reviewed refresh
  decisions that stay weaker than owner refresh laws and owner receipts
- reviewed closeout now aggregates every repo-scoped checkpoint ledger that shares the active runtime-session identity before it derives the closeout candidate map, so one narrow ledger cannot silently stand in for the whole session
- the runtime session store is now Codex-thread-aware when `CODEX_THREAD_ID` is available, so a new Codex thread rotates to a fresh session identity instead of silently reusing an older runtime file
- explicit checkpoint closeout now binds the live Codex rollout trace from that runtime session into `closeout-context.json` and reuses it as additional closeout evidence beside the reviewed artifact
- default auto checkpoint bridge from `aoa skills guard` when checkpoint-phase detection sees a real growth signal; `aoa skills enter` stays read-only unless `--checkpoint-kind` is explicit, and `aoa surfaces detect --append-note` remains the direct additive override
- explicit milestone checkpoint marking through `aoa checkpoint mark`, including public-share milestones such as `pr_opened`, `pr_merged`, and `owner_followthrough`, so agents do not have to re-enable ingress auto-append just to capture progress
- local managed-hook installation and status inspection for checkpoint-aware plain commits and git boundaries through `aoa checkpoint install-hook` and `aoa checkpoint hook-status`; the installed `post-commit` hook only triggers mid-session checkpoint capture and never runs closeout, promotion, harvest, push, or release logic, while `pre-push` and `pre-merge-commit` fail closed when any aggregated runtime-session checkpoint note still carries pending checkpoint reviews
- post-commit kind selection through `aoa checkpoint after-commit --kind auto|commit|owner_followthrough` and the hook's `AOA_CHECKPOINT_KIND`; `auto` keeps normal commits as `commit/code`, but owner-follow-through commit text or an already closed checkpoint note resolves to `owner_followthrough/public-share` without mutating or rotating the closed note, and an explicit reviewed-closeout owner follow-through can stay report-only once a matching owner-handoff already exists for the repo
- a commit is not complete from the agent workflow perspective until the hook-created checkpoint has a matching `aoa checkpoint review-note --auto` or richer manual review entry; scripts preserve the event boundary, while the agent still owns the semantic review
- `aoa checkpoint git-boundary-check` is the fail-closed control-plane surface behind the installed `pre-push` and `pre-merge-commit` hooks, and it stays active-session-only while reading the aggregated runtime-session checkpoint fan-in just like reviewed closeout does; quarantined legacy unscoped ledgers do not participate
- checkpoint closeout execution reports now declare `execution_mode=mechanical_bridge_artifact_build`, `mechanical_bridge_only=true`, and `agent_skill_application_required=true`, so generated packets cannot be mistaken for proof that a Codex agent has already applied the skill protocol to the full session
- checkpoint and explicit closeout surfaces keep canonical machine timestamps in UTC while also publishing local companion fields such as `observed_at_local`, `captured_at_local`, `built_at_local`, `executed_at_local`, and their matching `*_tz` labels for human review
- local CLI inspection surfaces that stay subordinate to source-owned meaning

## What it does not own

- It does not replace `aoa-routing`.
- It does not become the source of truth for skills, evals, memo, playbooks, agents, or KAG.
- It does not make `aoa skills detect/dispatch/enter/guard` mean anything other than skills.
- It does not become a service runtime or hidden monolith.

The SDK stays on the control plane: load, type, validate, activate, and hand off.

## Public support and release posture

For the shortest statement of what the SDK publicly supports, what an SDK release may honestly claim, and which CI tiers reinforce those claims, use `docs/RELEASE_CI_POSTURE.md`.

## Verify current repo state

Use this read-only/current-state battery:

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q
python -m ruff check .
aoa workspace inspect /srv/aoa-sdk
aoa compatibility check /srv/aoa-sdk
aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json
```

CI also reinforces this path with:

```bash
python -m mypy src
python -m build
```

## Current slice

```python
from aoa_sdk import AoASDK

sdk = AoASDK.from_workspace("/srv/aoa-sdk")

matches = sdk.routing.pick(kind="skill", query="bounded repo change")
preview = sdk.skills.disclose("aoa-change-protocol")
activation = sdk.skills.activate("aoa-change-protocol")
outer_ring = sdk.skills.project_core_outer_ring()
outer_ring_readiness = sdk.skills.project_core_outer_ring_readiness()
foundation = sdk.skills.project_foundation()
risk_ring = sdk.skills.project_risk_guard_ring()
risk_ring_governance = sdk.skills.project_risk_guard_ring_governance()
dispatch = sdk.skills.detect(
    repo_root="/srv/aoa-sdk",
    phase="ingress",
    intent_text="plan verify a bounded change",
)
surface_report = sdk.surfaces.detect(
    repo_root="/srv/aoa-sdk",
    phase="ingress",
    intent_text="verify recurring handoff proof",
)
stats_signal = sdk.stats.regrounding_signal(
    "surface_detection_summary",
    phase="pre-mutation",
    mutation_surface="code",
)
stats_route_hints = sdk.routing.stats_regrounding_hints(
    surface_name="surface_detection_summary",
)
checkpoint_report = sdk.surfaces.detect(
    repo_root="/srv/aoa-sdk",
    phase="checkpoint",
    checkpoint_kind="commit",
    intent_text="recurring owner follow-through after green verify",
)
checkpoint_skill_report = sdk.skills.detect(
    repo_root="/srv/aoa-sdk",
    phase="checkpoint",
    intent_text="plan verify a bounded change",
)
checkpoint_note = sdk.checkpoints.status(repo_root="/srv/aoa-sdk")
closeout_context = sdk.checkpoints.build_closeout_context(
    repo_root="/srv/aoa-sdk",
    reviewed_artifact_path="/srv/path/to/reviewed_session_artifact.md",
)
next_kernel_decision = closeout_context.followthrough_decision
closeout_execution = sdk.checkpoints.execute_closeout_chain(
    repo_root="/srv/aoa-sdk",
    reviewed_artifact_path="/srv/path/to/reviewed_session_artifact.md",
)
shortlist = sdk.routing.owner_layer_shortlist(signal="scenario-recurring")
surface_handoff = sdk.surfaces.build_closeout_handoff(
    surface_report,
    session_ref="session:2026-04-07-surface-first-wave",
)
verify_binding = sdk.agents.binding_for_phase("verify")
playbook = sdk.playbooks.get("bounded-change-safe")
memory = sdk.memo.recall(mode="semantic", query="charter")
eval_bundle = sdk.evals.inspect("aoa-bounded-change-quality")
automation = sdk.stats.automation_pipelines("pipeline:session-growth")
surface_stats = sdk.stats.surface_detection(window_date="2026-04-05")
deploy_status = sdk.codex.deploy_status()
kag = sdk.kag.inspect("AOA-K-0011")
rpg_build = sdk.rpg.latest_build("AOA-A-0002")
compatibility = sdk.compatibility.check_all()
```

The live read path already covers `aoa-routing`, `aoa-skills`, `aoa-agents`, `aoa-playbooks`, `aoa-memo`, `aoa-evals`, `aoa-stats`, and bounded `aoa-kag` inspect support.
The RPG addendum is also available as a typed consumer slice when its
canonical transport surfaces are present or fixture-staged.

## Workspace topology

- the usual editable federation root is `/srv`
- `abyss-stack` is the important exception: the source checkout lives at `~/src/abyss-stack`
- `/srv/abyss-stack` is a deployed runtime mirror, not the preferred source checkout
- `.aoa/workspace.toml` is the machine-readable workspace manifest

## Local commands

Inspect the resolved workspace layout:

```bash
aoa workspace inspect /srv/aoa-sdk
aoa workspace inspect /srv/aoa-sdk --json
```

Run the workspace-level Codex MCP server:

```bash
python -m pip install -e '.[mcp]'
python scripts/aoa_workspace_mcp_server.py
```

Plan or apply one portable sibling-workspace bootstrap:

```bash
aoa workspace bootstrap /work/my-aoa --json
aoa workspace bootstrap /work/my-aoa --execute --json
```

Check consumed surface compatibility across the local workspace:

```bash
aoa compatibility check /srv/aoa-sdk
aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json
python scripts/run_sibling_canary.py --repo-root . --matrix scripts/sibling_canary_matrix.json
```

Run one reviewed session closeout manifest:

```bash
aoa closeout run /srv/path/to/closeout.json --root /srv/aoa-sdk --json
```

Process the canonical closeout inbox:

```bash
aoa closeout process-inbox /srv/aoa-sdk --json
```

Queue one reviewed closeout manifest for automatic inbox processing:

```bash
aoa closeout submit-reviewed /srv/path/to/reviewed_session_artifact.md --session-ref session:2026-04-06-session-growth --receipt-dir /srv/path/to/receipts --root /srv/aoa-sdk --json
aoa closeout submit-reviewed /srv/path/to/W4-closeout.md --session-ref session:qwen-local-pilot-v1:W4:closeout --audit-ref /srv/path/to/W4-closeout.json --allow-empty --root /srv/aoa-sdk --json
aoa closeout build-manifest /srv/path/to/closeout.request.json --root /srv/aoa-sdk --enqueue --json
aoa closeout enqueue-current /srv/path/to/closeout.json --root /srv/aoa-sdk --json
aoa closeout status /srv/aoa-sdk --json
python scripts/install_closeout_units.py --overwrite --enable
```

Inspect one phase-aware foundation detection pass:

```bash
aoa skills detect /srv/aoa-sdk --phase ingress --intent-text "plan verify a bounded change" --root /srv/aoa-sdk --json
aoa skills detect /srv/aoa-sdk --phase checkpoint --intent-text "plan verify a bounded change" --root /srv/aoa-sdk --json
aoa skills dispatch /srv/aoa-sdk --phase pre-mutation --intent-text "refresh generated contracts" --mutation-surface repo-config --root /srv/aoa-sdk --json
```

Start one workspace session and persist the ingress/guard reports:

```bash
aoa skills enter /srv --intent-text "plan a cross-repo change" --root /srv --json
aoa skills enter /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --root /srv --json
aoa skills guard /srv/aoa-sdk --intent-text "regenerate compatibility surfaces" --mutation-surface repo-config --root /srv --json
aoa skills guard /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --mutation-surface code --root /srv --json
aoa skills guard /srv/aoa-sdk --intent-text "commit bounded patch" --mutation-surface code --root /srv --json
aoa skills guard /srv/aoa-sdk --intent-text "reviewable verify-green checkpoint" --mutation-surface code --checkpoint-kind verify_green --root /srv --json
aoa skills guard /srv/aoa-sdk --intent-text "refresh generated contracts" --mutation-surface code --no-auto-checkpoint --root /srv --json
```

Run one additive surface-detection pass without changing the skill-only lane:

```bash
aoa surfaces detect /srv/aoa-sdk --phase ingress --intent-text "verify recurring handoff proof" --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase pre-mutation --intent-text "prove and recall a recurring route" --mutation-surface code --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
```

Capture or promote one checkpoint-aware local note:

```bash
aoa checkpoint mark /srv/aoa-sdk --kind pr_opened --intent-text "opened PR after protected main rejected direct push" --mutation-surface public-share --root /srv/aoa-sdk --json
aoa checkpoint append /srv/aoa-sdk --kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa checkpoint after-commit /srv/aoa-sdk --commit-ref HEAD --root /srv --json
aoa checkpoint after-commit /srv/aoa-sdk --commit-ref HEAD --kind owner_followthrough --root /srv --json
aoa checkpoint review-note /srv/aoa-sdk --commit-ref HEAD --auto --root /srv --json
aoa checkpoint install-hook --repo aoa-sdk --hook all --root /srv --json
aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv --json
aoa checkpoint git-boundary-check /srv/aoa-sdk --boundary push --root /srv --json
aoa checkpoint build-closeout-context /srv/aoa-sdk --reviewed-artifact /srv/path/to/reviewed_session_artifact.md --root /srv/aoa-sdk --json
aoa checkpoint execute-closeout-chain /srv/aoa-sdk --reviewed-artifact /srv/path/to/reviewed_session_artifact.md --root /srv/aoa-sdk --json
aoa checkpoint status /srv/aoa-sdk --root /srv/aoa-sdk --json
aoa checkpoint promote /srv/aoa-sdk --target dionysus-note --root /srv/aoa-sdk --json
```

Build one reviewed-only closeout handoff from a persisted surface report:

```bash
aoa surfaces handoff /srv/aoa-sdk/.aoa/surface-detection/aoa-sdk.closeout.latest.json --session-ref session:2026-04-07-surface-first-wave --reviewed --root /srv/aoa-sdk --json
```

Install for development:

```bash
python -m pip install -e '.[dev]'
```

## Downstream consumers

The SDK is intended for downstream consumers such as `ATM10-Agent`, local scripts, notebooks, CI helpers, and future adapters that need typed access to AoA surfaces without scattering parsing glue across multiple projects.
