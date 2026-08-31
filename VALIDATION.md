# VALIDATION.md

Human on-demand procedure entrypoint for aoa-sdk.

This file is a procedure surface, not machine authority. The canonical repository-wide executable gate remains scripts/release_check.py; its owner-authored claim/evidence manifest, accepted validation graph, graph runner, and serial release_check.COMMANDS inventory remain authoritative. Nearest part VALIDATION.md files remain the source of exact part-local checks.

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

## Preserved local command procedures

The following exact command bodies were moved from active AGENTS.md procedure sections. Their source labels are provenance only; use the nearest applicable owner route and do not treat this archive as a replacement for the machine gate.

### Source `.aoa/AGENTS.md` — `Validate`

```bash
aoa workspace inspect /srv/aoa-sdk
python -m pytest -q
```

### Source `AGENTS.md` — `Inspection And Checkpoint Loop`

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

### Source `AGENTS.md` — `Verify`

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

### Source `AGENTS.md` — `Verify`

```bash
python -m mypy src
python -m build
python scripts/release_check.py
```

### Source `docs/AGENTS.md` — `Validation`

```bash
python -m pytest -q tests/test_docs_routes.py tests/test_design_surfaces.py
python scripts/validate_nested_agents.py
```

### Source `docs/decisions/AGENTS.md` — `Validation`

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_nested_agents.py
```

### Source `evals/AGENTS.md` — `Validation`

```bash
python ../aoa-evals/scripts/validate_local_eval_port.py --target-root .
```

### Source `generated/AGENTS.md` — `Validate`

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python scripts/build_source_topology_index.py --check
python scripts/validate_source_topology_index.py
python -m pytest -q
```

### Source `mechanics/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
```

### Source `mechanics/AGENTS.md` — `Validation`

```bash
python scripts/generate_decision_indexes.py --check
python -m pytest -q tests/test_mechanics_topology.py tests/test_validate_nested_agents.py
```

### Source `mechanics/agon/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python mechanics/agon/parts/gate-routing-bridge/scripts/build_agon_gate_routing_registry.py --check
python mechanics/agon/parts/gate-routing-bridge/scripts/validate_agon_gate_routing.py
python mechanics/agon/parts/center-law-preview-helpers/scripts/build_agon_ccs_sdk_helper_candidates.py --check
python mechanics/agon/parts/center-law-preview-helpers/scripts/validate_agon_ccs_sdk_helper_candidates.py
python mechanics/agon/parts/state-packet-review-bindings/scripts/build_agon_sdk_state_packet_bindings.py --check
python mechanics/agon/parts/state-packet-review-bindings/scripts/validate_agon_sdk_state_packet_bindings.py
python mechanics/agon/parts/recurrence-adapter/scripts/build_agon_recurrence_adapter_registry.py --check
python mechanics/agon/parts/recurrence-adapter/scripts/validate_agon_recurrence_adapter.py
python mechanics/agon/parts/recurrence-adapter/scripts/build_agon_recurrence_prebinding_review_lanes.py --check
python mechanics/agon/parts/recurrence-adapter/scripts/validate_agon_recurrence_prebinding_review_lanes.py
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/build_agon_duel_kernel_sdk_bindings.py --check
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/validate_agon_duel_kernel_sdk_bindings.py
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/build_agon_mechanical_trial_sdk_helpers.py --check
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/validate_agon_mechanical_trial_sdk_helpers.py
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/build_agon_vds_sdk_helper_candidates.py --check
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/validate_agon_vds_sdk_helper_candidates.py
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/build_agon_retention_rank_sdk_helpers.py --check
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/validate_agon_retention_rank_sdk_helpers.py
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/build_agon_epistemic_sdk_helpers.py --check
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/validate_agon_epistemic_sdk_helpers.py
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/build_agon_kag_sdk_helpers.py --check
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/validate_agon_kag_sdk_helpers.py
python mechanics/agon/parts/school-lineage-campaign-review-helpers/scripts/build_agon_slc_sdk_helpers.py --check
python mechanics/agon/parts/school-lineage-campaign-review-helpers/scripts/validate_agon_slc_sdk_helpers.py
python mechanics/agon/parts/sophian-threshold-review-helpers/scripts/build_agon_sophian_sdk_helpers.py --check
python mechanics/agon/parts/sophian-threshold-review-helpers/scripts/validate_agon_sophian_sdk_helpers.py
python -m pytest -q mechanics/agon/parts/gate-routing-bridge/tests/test_agon_gate_routing_bridge.py mechanics/agon/parts/center-law-preview-helpers/tests/test_agon_ccs_sdk_helper_candidates.py mechanics/agon/parts/state-packet-review-bindings/tests/test_agon_sdk_state_packet_bindings.py mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_adapter.py mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_prebinding_review_lanes.py mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_duel_kernel_sdk_bindings.py mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_mechanical_trial_sdk_helpers.py mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_vds_sdk_helper_candidates.py mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_retention_rank_sdk_helpers.py mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_epistemic_sdk_helpers.py mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_kag_sdk_helpers.py mechanics/agon/parts/school-lineage-campaign-review-helpers/tests/test_agon_slc_sdk_helpers.py mechanics/agon/parts/sophian-threshold-review-helpers/tests/test_agon_sophian_sdk_helpers.py
```

### Source `mechanics/agon/parts/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
```

### Source `mechanics/antifragility/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/antifragility/parts/stress-posture-dispatch-gate/tests/test_stress_posture_dispatch_gate.py mechanics/antifragility/parts/reviewed-stress-closeout-carry/tests/test_reviewed_stress_closeout_carry.py mechanics/antifragility/parts/via-negativa/tests/test_via_negativa_checklist.py
```

### Source `mechanics/antifragility/parts/AGENTS.md` — `Validation`

```bash
python -m pytest -q mechanics/antifragility/parts/stress-posture-dispatch-gate/tests/test_stress_posture_dispatch_gate.py mechanics/antifragility/parts/reviewed-stress-closeout-carry/tests/test_reviewed_stress_closeout_carry.py mechanics/antifragility/parts/via-negativa/tests/test_via_negativa_checklist.py
python scripts/validate_mechanics_topology.py
```

### Source `mechanics/boundary-bridge/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_agent_phase_binding_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_eval_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_memo_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector.py mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector_cli.py
```

### Source `mechanics/boundary-bridge/legacy/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

### Source `mechanics/checkpoint/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_lifecycle_indexes.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_session_memory.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_candidate_intelligence.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_carrier_intelligence.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_reviewed_closeout_context_carry.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_component_refresh_followthrough.py
aoa checkpoint lifecycle-audit /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json
aoa checkpoint backlog-audit /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --write-index --json
aoa checkpoint close-archive /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json
aoa checkpoint reconcile-sessions /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json
aoa checkpoint candidate-intelligence /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --sample-limit 3 --write-index --json
```

### Source `mechanics/checkpoint/legacy/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

### Source `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/AGENTS.md` — `Validate`

```bash
aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv/AbyssOS --json
python -m pytest -q
```

### Source `mechanics/codex-projection/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py
```

### Source `mechanics/codex-projection/legacy/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

### Source `mechanics/codex-projection/parts/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py
```

### Source `mechanics/experience/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/experience/parts/capture-pipeline-helper/tests/test_capture_pipeline_helper.py
python -m pytest -q mechanics/experience/parts/adoption-federation-helper-contracts/tests/test_adoption_federation_helper_contracts.py
python -m pytest -q mechanics/experience/parts/deployment-watchtower-helper-contracts/tests/test_deployment_watchtower_helper_contracts.py
python -m pytest -q mechanics/experience/parts/governance-runtime-helper-contracts/tests/test_governance_runtime_helper_contracts.py
python -m pytest -q mechanics/experience/parts/office-release-train-helper-contracts/tests/test_office_release_train_helper_contracts.py
```

### Source `mechanics/experience/parts/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
```

### Source `mechanics/questbook/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py --strict-advisory --fail-on-untracked
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
```

### Source `mechanics/questbook/parts/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
```

### Source `mechanics/recurrence/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python mechanics/recurrence/parts/component-manifest-gate/scripts/validate_recurrence_manifests.py --workspace-root /srv/AbyssOS --json
python -m pytest -q mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_registry.py mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_seed.py
```

### Source `mechanics/recurrence/parts/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

### Source `mechanics/release-support/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python scripts/release_check.py
python -m pytest -q mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py
```

### Source `mechanics/rpg/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/rpg/parts/typed-consumer-api/tests/test_typed_consumer_api.py mechanics/rpg/parts/surface-path-transport/tests/test_surface_path_transport.py
```

### Source `mechanics/rpg/parts/AGENTS.md` — `Validation`

```bash
python -m pytest -q mechanics/rpg/parts/typed-consumer-api/tests/test_typed_consumer_api.py mechanics/rpg/parts/surface-path-transport/tests/test_surface_path_transport.py
python scripts/validate_mechanics_topology.py
```

### Source `mechanics/runtime-seam/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution.py mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests/test_portable_workspace_bootstrap_cli.py mechanics/runtime-seam/parts/control-plane-capsule/tests/test_control_plane_capsule.py mechanics/runtime-seam/parts/runtime-mirror-boundary/tests/test_runtime_mirror_boundary.py
```

### Source `mechanics/runtime-seam/legacy/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

### Source `mechanics/titan/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/tests/test_titanctl_runtime.py mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/tests/test_titan_incarnation_spine.py
python -m pytest -q mechanics/titan/parts/operator-console-helper-contracts/tests/test_titan_console.py mechanics/titan/parts/appserver-bridge-helper-contracts/tests/test_titan_appserver_bridge.py mechanics/titan/parts/memory-loom-recall-helper-contracts/tests/test_titan_memory_loom.py mechanics/titan/parts/session-praxis-replay-helper-contracts/tests/test_titan_session_replay.py mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/tests/test_titan_swarm_ledger.py mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/tests/test_titan_closeout_audit.py
```

### Source `mechanics/titan/parts/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
```

### Source `quests/AGENTS.md` — `Validation`

```bash
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py --strict-advisory --fail-on-untracked
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
```

### Source `schemas/AGENTS.md` — `Validate`

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q
```

### Source `scripts/AGENTS.md` — `Validation`

```bash
python -m ruff check scripts
python scripts/validate_sdk_source_home.py
python scripts/validate_mechanics_topology.py
python scripts/build_source_topology_index.py --check
python scripts/validate_source_topology_index.py
python scripts/release_check.py
```

### Source `sdk/AGENTS.md` — `Validation`

```bash
python scripts/validate_sdk_source_home.py
python scripts/validate_nested_agents.py --strict-advisory --fail-on-untracked
python -m pytest -q tests/test_sdk_source_home.py tests/test_design_surfaces.py
```

### Source `sdk/distribution/AGENTS.md` — `Validation`

```bash
python scripts/validate_sdk_source_home.py
python scripts/release_check.py
python -m build
```

### Source `sdk/facade-boundary/AGENTS.md` — `Validation`

```bash
python scripts/validate_sdk_source_home.py
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests
```

### Source `sdk/public-interface/AGENTS.md` — `Validation`

```bash
python scripts/validate_sdk_source_home.py
python -m pytest -q tests/test_sdk_source_home.py
python -m pytest -q
```

### Source `sdk/runtime-entry/AGENTS.md` — `Validation`

```bash
python scripts/validate_sdk_source_home.py
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python scripts/validate_mechanics_topology.py
```

### Source `src/aoa_sdk/AGENTS.md` — `Validate`

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q
python -m ruff check .
```

### Source `stats/AGENTS.md` — `Validation`

```bash
PYTHONPATH=src python -c 'from aoa_sdk.compatibility.policy import SURFACE_COMPATIBILITY_RULES as rules; versioned=[key for key, rule in rules.items() if rule.version_field is not None]; unversioned=[key for key, rule in rules.items() if rule.version_field is None]; print({"population": len(rules), "versioned": len(versioned), "ratio": len(versioned) / len(rules), "unversioned": unversioned})'
```

### Source `stats/AGENTS.md` — `Validation`

```bash
python scripts/validate_local_stats_port.py
```

### Source `tests/AGENTS.md` — `Validation`

```bash
python -m pytest -q tests
python scripts/validate_mechanics_topology.py
```

## Preserved inline procedure references

Inline command tokens and standalone procedure lines removed from inherited cards remain verbatim here for provenance and on-demand lookup.

- `AGENTS.md`: `aoa skills ...`
- `AGENTS.md`: `python scripts/release_check.py`
- `AGENTS.md`: `python scripts/release_check.py --mode serial`
- `mechanics/AGENTS.md`: `python scripts/release_check.py`
