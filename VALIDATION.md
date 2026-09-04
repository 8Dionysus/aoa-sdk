# VALIDATION.md

Human on-demand procedure entrypoint for aoa-sdk.

This file is a procedure surface, not machine authority. The canonical
repository-wide executable gate remains `scripts/release_check.py`; its
owner-authored claim/evidence manifest, accepted validation graph, graph
runner, and serial `release_check.COMMANDS` inventory remain authoritative.
Part `VALIDATION.md` files either own exact part-local checks or route to the
singular root or cross-part procedure that owns them.

Use the narrowest applicable section for the touched path, semantic question, or requested operation. Preserve command order, environment, warnings, and receipt identity when using a retained battery.

## Repository inspection

Run read-only scope checks before and after a change:

```bash
git status --short --branch
git rev-parse HEAD
git diff --check
git diff --stat
```

Confirm the intended worktree and required source HEAD before any bounded edit; do not use this route to mutate sibling or live surfaces.

## Focused repository checks

The focused repository battery is retained in this exact order:

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

## Release-facing and full owner checks

For release or CI-facing surfaces, retain this exact supplemental order:

```bash
python -m mypy src
python -m build
python scripts/release_check.py
```

scripts/release_check.py selects the accepted full claim/evidence graph. Use scripts/release_check.py --mode serial only for the retained exact completeness oracle, rollback, or an explicit comparison run.

## Serial completeness and rollback

The serial route is an exact oracle and rollback procedure; do not reorder, shorten, or infer success from a partial subset:

```bash
python scripts/release_check.py --mode serial
```

When an identity-bound receipt is required, use the owner-approved receipt path and preserve the graph configuration at mechanics/release-support/parts/validation-evidence-graph/config/validation_graph.json.

## Inspection and checkpoint review

These procedures are session-local and owner-subordinate. Passive skill inspection does not select, activate, dispatch, or create skill-session state; checkpoint outputs do not become proof, memory, progression, or owner verdicts. Run only under the applicable owner and operator scope:

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

skipped_no_active_session and agent_review=pending are not final review; capability_execution_claimed=false remains explicit through materialization and A2A return.

## Landing procedure

Root AGENTS.md owns the repository-wide branch, PR, CI, and merge route. .github/AGENTS.md owns the GitHub-native files that support it.

When the operator explicitly requests landing, use this route:

1. Start from a branch based on the current origin/main. If the worktree is already dirty, inventory it first and carry forward only the intended diff.
2. Commit the intended change with a message that names the changed surface.
3. Push the branch and open a pull request that states changed surfaces, validation run, skipped checks, and remaining risk.
4. Wait for GitHub Repo Validation and any required GitHub checks. If a check fails, fix the branch and wait for the new result.
5. Merge through GitHub after green validation. Use squash unless repository settings report a different required method; report the method that landed.
6. Return to main, fast-forward from origin/main, and confirm the worktree is clean before closeout.

If GitHub status or merge permissions cannot be observed, stop the landing route and report the exact blocker instead of guessing.

This bounded documentation lane does not push, open PRs, wait on CI, merge, or alter sibling/live state.

## Active owner routes

The root lanes above own repository-wide inspection, focused checks, release
checks, serial completeness, checkpoint review, and landing. Part-specific
routes are exposed by the nearest `VALIDATION.md`; they either own exact checks
or link to the singular root or cross-part procedure. Examples include
[Agon center-law](mechanics/agon/parts/center-law-preview-helpers/VALIDATION.md#narrow-checks),
[Boundary runner](mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/VALIDATION.md),
[Checkpoint growth](mechanics/checkpoint/parts/session-growth-checkpoint-cycle/VALIDATION.md),
[Codex workspace MCP](mechanics/codex-projection/parts/workspace-mcp-server/VALIDATION.md),
[Recurrence manifest](mechanics/recurrence/parts/component-manifest-gate/VALIDATION.md),
[Release support](mechanics/release-support/parts/public-support-ci-posture/VALIDATION.md),
[RPG consumer](mechanics/rpg/parts/typed-consumer-api/VALIDATION.md),
[Runtime capsule](mechanics/runtime-seam/parts/control-plane-capsule/VALIDATION.md),
and [Titan helpers](mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/VALIDATION.md).
These owner surfaces replace inherited copies; the accepted validation graph and
its manifest remain the composition authority.

## Cross-part routing suites

These cross-part routes are composed here so their exact executable procedures
remain owned once while the participating leaf surfaces link back to this lane:

```bash
python -m pytest -q tests/test_docs_routes.py
python -m pytest -q tests/test_docs_routes.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py
python -m pytest -q tests/test_docs_routes.py mechanics/runtime-seam/parts/control-plane-capsule/tests/test_control_plane_capsule.py
```

## Additional repository-wide procedures

These exact procedures have no narrower `VALIDATION.md` owner. They remain here
once, in their original command spelling and order, for targeted route use:

```bash
aoa workspace inspect /srv/aoa-sdk
python -m pytest -q tests
python -m pytest -q tests/test_docs_routes.py tests/test_design_surfaces.py
python -m pytest -q tests/test_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
python -m pytest -q tests/test_mechanics_topology.py tests/test_validate_nested_agents.py
python -m pytest -q tests/test_sdk_source_home.py
python -m pytest -q tests/test_sdk_source_home.py tests/test_design_surfaces.py
python -m ruff check scripts
python ../aoa-evals/scripts/validate_local_eval_port.py --target-root .
python scripts/validate_nested_agents.py
python scripts/validate_nested_agents.py --strict-advisory --fail-on-untracked
PYTHONPATH=src python -c 'from aoa_sdk.compatibility.policy import SURFACE_COMPATIBILITY_RULES as rules; versioned=[key for key, rule in rules.items() if rule.version_field is not None]; unversioned=[key for key, rule in rules.items() if rule.version_field is None]; print({"population": len(rules), "versioned": len(versioned), "ratio": len(versioned) / len(rules), "unversioned": unversioned})'
```

The following family-level suite invocations are owned here as composition
routes. Participating part surfaces link back to this lane when repeating the
same invocation would create a second human procedure owner:

```bash
python -m pytest -q mechanics/agon/parts/gate-routing-bridge/tests/test_agon_gate_routing_bridge.py mechanics/agon/parts/center-law-preview-helpers/tests/test_agon_ccs_sdk_helper_candidates.py mechanics/agon/parts/state-packet-review-bindings/tests/test_agon_sdk_state_packet_bindings.py mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_adapter.py mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_prebinding_review_lanes.py mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_duel_kernel_sdk_bindings.py mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_mechanical_trial_sdk_helpers.py mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_vds_sdk_helper_candidates.py mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_retention_rank_sdk_helpers.py mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_epistemic_sdk_helpers.py mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_kag_sdk_helpers.py mechanics/agon/parts/school-lineage-campaign-review-helpers/tests/test_agon_slc_sdk_helpers.py mechanics/agon/parts/sophian-threshold-review-helpers/tests/test_agon_sophian_sdk_helpers.py
python -m pytest -q mechanics/antifragility/parts/stress-posture-dispatch-gate/tests/test_stress_posture_dispatch_gate.py mechanics/antifragility/parts/reviewed-stress-closeout-carry/tests/test_reviewed_stress_closeout_carry.py mechanics/antifragility/parts/via-negativa/tests/test_via_negativa_checklist.py
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_agent_phase_binding_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_eval_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_memo_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector.py mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector_cli.py
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_lifecycle_indexes.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_session_memory.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_candidate_intelligence.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_carrier_intelligence.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_reviewed_closeout_context_carry.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_component_refresh_followthrough.py
python -m pytest -q mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py
python -m pytest -q mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_registry.py mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_seed.py
python -m pytest -q mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py
python -m pytest -q mechanics/rpg/parts/typed-consumer-api/tests/test_typed_consumer_api.py mechanics/rpg/parts/surface-path-transport/tests/test_surface_path_transport.py
python -m pytest -q mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution.py mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests/test_portable_workspace_bootstrap_cli.py mechanics/runtime-seam/parts/control-plane-capsule/tests/test_control_plane_capsule.py mechanics/runtime-seam/parts/runtime-mirror-boundary/tests/test_runtime_mirror_boundary.py
python -m pytest -q mechanics/titan/parts/operator-console-helper-contracts/tests/test_titan_console.py mechanics/titan/parts/appserver-bridge-helper-contracts/tests/test_titan_appserver_bridge.py mechanics/titan/parts/memory-loom-recall-helper-contracts/tests/test_titan_memory_loom.py mechanics/titan/parts/session-praxis-replay-helper-contracts/tests/test_titan_session_replay.py mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/tests/test_titan_swarm_ledger.py mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/tests/test_titan_closeout_audit.py
```
