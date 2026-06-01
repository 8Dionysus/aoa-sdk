# SDK Mechanic Artifact Topology

## Purpose

`mechanics/` is no longer only an outline map.

This surface defines where mechanic-owned artifacts live as root payload moves
into functioning part homes. It owns placement law and migration accounting. It
does not replace package cards, source code, schemas, generated companions,
validators, decisions, or sibling-owner truth.

## Root Technical Districts

Root technical districts remain valid only when an artifact is repo-wide,
public-contract-shaped, shared across multiple mechanics, or required at a
stable tooling path.

| District | Root-owned when |
| --- | --- |
| `docs/` | repo-wide boundary, design, release, workspace, decision, or public route docs |
| `schemas/` | shared public SDK contracts or cross-mechanic/root-published generated contracts |
| `examples/` | shared public examples or cross-mechanic fixtures |
| `config/` | repo-wide builder input or shared control-plane configuration |
| `generated/` | root-published compact companion consumed outside one mechanic |
| `manifests/` | shared recurrence manifests that are not package-local |
| `quests/` | Questbook source quest records in lane/state form; helper payload and helper contracts stay part-local |
| `scripts/` | release gates, repo-wide validators, shared builders, or operator utilities |
| `tests/` | repo-wide regression, shared fixtures, or cross-mechanic checks |

Root districts must not keep convenience aliases for mechanic-owned payload.
If a root path remains for tooling, it must be a thin compatibility entrypoint
or root-published output with a documented owner and validator.

`scripts/validate_mechanics_topology.py` enforces this as an active allowlist:
current root `docs/`, `generated/`, `schemas/`, `scripts/`, and `tests/`
files must be explicitly named, while `config/`, `examples/`, `manifests/`,
`githooks/`, and `systemd/` stay absent unless a new decision-backed root
contract reopens them. Root `quests/` is the reopened Questbook source-store
contract and must keep lane/state source records instead of helper payload.
The default route for new
mechanic-owned payload is a part-local path whose name exposes owner,
operation, artifact kind, next route, and validation home.

## Part-Local Artifact Lane

Single-mechanic artifacts live under the owning functioning part:

```text
mechanics/<parent>/parts/<part>/
  README.md
  CONTRACT.md
  VALIDATION.md
  config/
  docs/
  examples/
  generated/
  manifests/
  schemas/
  scripts/
  tests/
```

The path must say what an agent needs to know: operation, part role, artifact
kind, owner, next route, and validation home.

## Legacy Posture

Legacy is provenance only.

Historical names, old root paths, and former parent candidates may appear in
`PROVENANCE.md`, migration receipts, legacy indexes, or compatibility
accounting. They must not remain active routes. The active route is
the part-local path or an explicitly documented root public/tooling contract.

## Current Migration Ledger

| Old root path family | Active home | Owner | Status | Validation |
| --- | --- | --- | --- | --- |
| `config/agon_recurrence_adapter.seed.json`, `config/agon_recurrence_prebinding_review_lanes.seed.json` | `mechanics/agon/parts/recurrence-adapter/config/` | `agon/recurrence-adapter` | moved | `mechanics/agon/parts/recurrence-adapter/VALIDATION.md` |
| `docs/AGON_RECURRENCE_ADAPTER*.md`, `docs/AGON_RECURRENCE_REVIEW_LANES.md`, `docs/AGON_RECURRENCE_STOP_LINES.md`, `docs/prebinding-review-lanes.md` | `mechanics/agon/parts/recurrence-adapter/docs/` | `agon/recurrence-adapter` | moved | `mechanics/agon/parts/recurrence-adapter/VALIDATION.md` |
| `schemas/agon_recurrence_adapter.schema.json`, `schemas/agon-recurrence-adapter-registry.schema.json`, `schemas/agon-recurrence-prebinding-review-lanes.schema.json` | `mechanics/agon/parts/recurrence-adapter/schemas/` | `agon/recurrence-adapter` | moved | `mechanics/agon/parts/recurrence-adapter/VALIDATION.md` |
| `generated/agon_recurrence_adapter_registry.min.json`, `generated/agon_recurrence_prebinding_review_lanes.min.json` | `mechanics/agon/parts/recurrence-adapter/generated/` | `agon/recurrence-adapter` | moved | `mechanics/agon/parts/recurrence-adapter/VALIDATION.md` |
| `scripts/build_agon_recurrence_adapter_registry.py`, `scripts/validate_agon_recurrence_adapter.py`, `scripts/build_agon_recurrence_prebinding_review_lanes.py`, `scripts/validate_agon_recurrence_prebinding_review_lanes.py` | `mechanics/agon/parts/recurrence-adapter/scripts/` | `agon/recurrence-adapter` | moved | `mechanics/agon/parts/recurrence-adapter/VALIDATION.md` |
| `tests/test_agon_recurrence_adapter.py`, `tests/test_agon_recurrence_prebinding_review_lanes.py` | `mechanics/agon/parts/recurrence-adapter/tests/` | `agon/recurrence-adapter` | moved | `mechanics/agon/parts/recurrence-adapter/VALIDATION.md` |
| Agon helper quest source records | `quests/agon/ready/` | `questbook/quest-source-store` with helper contracts under `mechanics/agon/parts/*` | restored root source store | `mechanics/questbook/parts/quest-source-store/VALIDATION.md` |
| CCS helper candidate config, docs, schemas, example, generated registry, quest, scripts, and test | `mechanics/agon/parts/center-law-preview-helpers/` | `agon/center-law-preview-helpers` | moved | `mechanics/agon/parts/center-law-preview-helpers/VALIDATION.md` |
| state-packet, sealed-commit, and packet stop-line config, docs, schemas, example, generated registry, quest, scripts, and test | `mechanics/agon/parts/state-packet-review-bindings/` | `agon/state-packet-review-bindings` | moved | `mechanics/agon/parts/state-packet-review-bindings/VALIDATION.md` |
| duel-kernel and mechanical-trial config, docs, schemas, examples, generated registries, quests, scripts, and tests | `mechanics/agon/parts/duel-kernel-review-bindings/` | `agon/duel-kernel-review-bindings` | moved | `mechanics/agon/parts/duel-kernel-review-bindings/VALIDATION.md` |
| VDS plus retention/rank config, docs, schemas, examples, generated registries, quests, scripts, and tests | `mechanics/agon/parts/verdict-retention-rank-review-helpers/` | `agon/verdict-retention-rank-review-helpers` | moved | `mechanics/agon/parts/verdict-retention-rank-review-helpers/VALIDATION.md` |
| epistemic plus KAG config, docs, schemas, examples, generated registries, quests, scripts, and tests | `mechanics/agon/parts/epistemic-kag-review-helpers/` | `agon/epistemic-kag-review-helpers` | moved | `mechanics/agon/parts/epistemic-kag-review-helpers/VALIDATION.md` |
| SLC config, docs, schemas, example, generated registry, quest, scripts, and test | `mechanics/agon/parts/school-lineage-campaign-review-helpers/` | `agon/school-lineage-campaign-review-helpers` | moved | `mechanics/agon/parts/school-lineage-campaign-review-helpers/VALIDATION.md` |
| Sophian threshold config, docs, schemas, example, generated registry, quest, scripts, and test | `mechanics/agon/parts/sophian-threshold-review-helpers/` | `agon/sophian-threshold-review-helpers` | moved | `mechanics/agon/parts/sophian-threshold-review-helpers/VALIDATION.md` |
| `docs/AGON_WAVE1_EXPERIENCE_CAPTURE_PIPELINE.md`, `schemas/agon-experience-capture-pipeline-helper.schema.json`, `examples/agon_experience_capture_pipeline_helper.example.json`, `tests/test_agon_experience_capture_pipeline_helper.py` | `mechanics/experience/parts/capture-pipeline-helper/` | `experience/capture-pipeline-helper` | moved | `mechanics/experience/parts/capture-pipeline-helper/VALIDATION.md` |
| adoption, shadow-run, federation, harvest, pattern, KAG, and ToS dossier docs, schemas, examples, and seed tests | `mechanics/experience/parts/adoption-federation-helper-contracts/` | `experience/adoption-federation-helper-contracts` | moved | `mechanics/experience/parts/adoption-federation-helper-contracts/VALIDATION.md` |
| certification, deployment, regression, release-candidate, rollback, and watchtower docs, schemas, examples, and seed tests | `mechanics/experience/parts/deployment-watchtower-helper-contracts/` | `experience/deployment-watchtower-helper-contracts` | moved | `mechanics/experience/parts/deployment-watchtower-helper-contracts/VALIDATION.md` |
| governance, council, appeal, veto, constitution-runtime, queue, sealing, and replay docs, schemas, examples, and seed tests | `mechanics/experience/parts/governance-runtime-helper-contracts/` | `experience/governance-runtime-helper-contracts` | moved | `mechanics/experience/parts/governance-runtime-helper-contracts/VALIDATION.md` |
| installation, console, sovereign release, handoff graph, office registry, and office train docs, schemas, examples, and seed tests | `mechanics/experience/parts/office-release-train-helper-contracts/` | `experience/office-release-train-helper-contracts` | moved | `mechanics/experience/parts/office-release-train-helper-contracts/VALIDATION.md` |
| `docs/CODEX_PLANE_DEPLOY_STATUS.md` | `mechanics/codex-projection/parts/live-rollout-status-readout/docs/live-rollout-status-readout.md` | `codex-projection/live-rollout-status-readout` | moved | `mechanics/codex-projection/parts/live-rollout-status-readout/VALIDATION.md` |
| `schemas/codex_plane_deploy_status_snapshot_v1.json` | `mechanics/codex-projection/parts/live-rollout-status-readout/schemas/live-rollout-status-snapshot.schema.json` | `codex-projection/live-rollout-status-readout` | moved | `mechanics/codex-projection/parts/live-rollout-status-readout/VALIDATION.md` |
| `examples/codex_plane_deploy_status_snapshot.example.json` | `mechanics/codex-projection/parts/live-rollout-status-readout/examples/live-rollout-status-snapshot.example.json` | `codex-projection/live-rollout-status-readout` | moved | `mechanics/codex-projection/parts/live-rollout-status-readout/VALIDATION.md` |
| `tests/test_codex_deploy_status.py` | `mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py` | `codex-projection/live-rollout-status-readout` | moved | `mechanics/codex-projection/parts/live-rollout-status-readout/VALIDATION.md` |
| `docs/codex-workspace-mcp.md`, `scripts/aoa_workspace_mcp_server.py`, and `tests/test_codex_workspace_mcp.py` | `mechanics/codex-projection/parts/workspace-mcp-server/` | `codex-projection/workspace-mcp-server` | moved | `mechanics/codex-projection/parts/workspace-mcp-server/VALIDATION.md` |
| `docs/CODEX_PLANE_PORTABILITY.md` | `mechanics/codex-projection/parts/portability-boundary/docs/portability-boundary.md` | `codex-projection/portability-boundary` | moved | `mechanics/codex-projection/parts/portability-boundary/VALIDATION.md` |
| `docs/CODEX_DEPLOY_OPERATION_BOUNDARY_NOTE.md`, `docs/codex_rollout_campaign_refs.md` | `mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/` | `codex-projection/owner-rollout-reference-handoff` | moved | `mechanics/codex-projection/parts/owner-rollout-reference-handoff/VALIDATION.md` |
| `tests/test_workspace.py` | `mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution.py` | `runtime-seam/workspace-root-resolution` | moved | `mechanics/runtime-seam/parts/workspace-root-resolution/VALIDATION.md` |
| workspace inspect CLI cases from `tests/test_cli.py` | `mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py` | `runtime-seam/workspace-root-resolution` | moved | `mechanics/runtime-seam/parts/workspace-root-resolution/VALIDATION.md` |
| workspace bootstrap CLI cases from `tests/test_cli.py` | `mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests/test_portable_workspace_bootstrap_cli.py` | `runtime-seam/portable-workspace-bootstrap` | moved | `mechanics/runtime-seam/parts/portable-workspace-bootstrap/VALIDATION.md` |
| `tests/test_workspace_control_plane.py` | `mechanics/runtime-seam/parts/control-plane-capsule/tests/test_control_plane_capsule.py` | `runtime-seam/control-plane-capsule` | moved | `mechanics/runtime-seam/parts/control-plane-capsule/VALIDATION.md` |
| `tests/test_live_workspace.py` | `mechanics/runtime-seam/parts/runtime-mirror-boundary/tests/test_runtime_mirror_boundary.py` | `runtime-seam/runtime-mirror-boundary` | moved | `mechanics/runtime-seam/parts/runtime-mirror-boundary/VALIDATION.md` |
| sibling facade and compatibility tests from `tests/test_agents.py`, `tests/test_compatibility.py`, `tests/test_evals.py`, `tests/test_governed_runs.py`, `tests/test_kag.py`, `tests/test_memo.py`, `tests/test_playbooks.py`, `tests/test_routing.py`, and `tests/test_stats.py` | `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/` | `boundary-bridge/consumed-surface-posture-gate` | moved | `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/VALIDATION.md` |
| compatibility CLI cases from `tests/test_cli.py` | `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py` | `boundary-bridge/consumed-surface-posture-gate` | moved | `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/VALIDATION.md` |
| `docs/skill-runtime-recommendation-gap.md`, `docs/skill-runtime-recommendation-gap-fix-spec.md`, and `tests/test_skills.py` | `mechanics/boundary-bridge/parts/skill-runtime-bridge/` | `boundary-bridge/skill-runtime-bridge` | moved | `mechanics/boundary-bridge/parts/skill-runtime-bridge/VALIDATION.md` |
| `tests/test_skill_reference_contracts.py` | `mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_reference_contracts.py` | `boundary-bridge/skill-runtime-bridge` | moved | `mechanics/boundary-bridge/parts/skill-runtime-bridge/VALIDATION.md` |
| skill CLI cases from `tests/test_cli.py` | `mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py` | `boundary-bridge/skill-runtime-bridge` | moved | `mechanics/boundary-bridge/parts/skill-runtime-bridge/VALIDATION.md` |
| `tests/test_techniques.py` | `mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/tests/test_technique_promotion_readiness_reader.py` | `boundary-bridge/technique-promotion-readiness-reader` | moved | `mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/VALIDATION.md` |
| surface detection boundary, enrichment, heuristics, closeout handoff docs, and surface detection tests | `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/` | `boundary-bridge/owner-layer-signal-handoff` | moved | `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/VALIDATION.md` |
| A2A summon/return/checkpoint docs, examples, fixture, SDK API tests, skill-contract tests, assessment tests, return tests, closeout tests, and E2E fixture tests | `mechanics/checkpoint/parts/child-task-reentry/` | `checkpoint/child-task-reentry` | moved | `mechanics/checkpoint/parts/child-task-reentry/VALIDATION.md` |
| `docs/session-growth-checkpoints.md` and `docs/checkpoint-note-promotion.md` | `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/` | `checkpoint/session-growth-checkpoint-cycle` | moved | `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/VALIDATION.md` |
| `tests/test_checkpoint_cli.py` and `tests/test_checkpoints.py` | `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/` | `checkpoint/session-growth-checkpoint-cycle` | moved | `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/VALIDATION.md` |
| `tests/test_dirty_gate.py` | `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py` | `checkpoint/session-growth-checkpoint-cycle` | moved | `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/VALIDATION.md` |
| `githooks/post-commit`, `githooks/pre-push`, and `githooks/pre-merge-commit` | `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/` | `checkpoint/session-growth-checkpoint-cycle` | moved; hook filenames stay Git-native under the part-local owner route | `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/VALIDATION.md` |
| `docs/session-closeout.md`, `scripts/install_closeout_units.py`, and `scripts/process_closeout_inbox.py` | `mechanics/checkpoint/parts/reviewed-session-handoff-runner/` | `checkpoint/reviewed-session-handoff-runner` | moved | `mechanics/checkpoint/parts/reviewed-session-handoff-runner/VALIDATION.md` |
| `systemd/aoa-closeout-inbox.path` and `systemd/aoa-closeout-inbox.service` | `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/` | `checkpoint/reviewed-session-handoff-runner` | moved; unit filenames stay systemd-native under the part-local owner route | `mechanics/checkpoint/parts/reviewed-session-handoff-runner/VALIDATION.md` |
| `tests/test_closeout.py` and closeout CLI cases from `tests/test_cli.py` | `mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py` | `checkpoint/reviewed-session-handoff-runner` | moved | `mechanics/checkpoint/parts/reviewed-session-handoff-runner/VALIDATION.md` |
| `docs/CANDIDATE_LINEAGE_CARRY.md`, `docs/closeout-followthrough-map.md`, `docs/COMPONENT_DRIFT_HINTS.md`, `docs/SELF_AGENCY_CONTINUITY_CARRY.md`, `docs/SESSION_GROWTH_KERNEL_SIGNAL_RULES.md` | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/` | `checkpoint/reviewed-closeout-context-carry` | moved | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/VALIDATION.md` |
| checkpoint closeout-carry schemas: `checkpoint_lineage_hint`, `closeout_candidate_lineage_map`, `closeout_owner_followthrough_map`, `component_drift_hint_set`, `component_refresh_followthrough_decision_set`, `closeout_continuity_window`, and `closeout_followthrough_decision` | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/schemas/` | `checkpoint/reviewed-closeout-context-carry` | moved | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/VALIDATION.md` |
| checkpoint closeout-carry examples and context fixtures | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/examples/` | `checkpoint/reviewed-closeout-context-carry` | moved | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/VALIDATION.md` |
| `tests/test_candidate_lineage_examples.py` and `tests/test_component_refresh_examples.py` | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/` | `checkpoint/reviewed-closeout-context-carry` | moved | `mechanics/checkpoint/parts/reviewed-closeout-context-carry/VALIDATION.md` |
| Titan runtime harness, incarnation spine, identity ledger, session ingress, gate, receipt, and lineage docs, schemas, examples, scripts, and tests | `mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/` | `titan/incarnation-identity-runtime-helper-contracts` | moved | `mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/VALIDATION.md` |
| Titan operator console docs, schemas, examples, script, and test | `mechanics/titan/parts/operator-console-helper-contracts/` | `titan/operator-console-helper-contracts` | moved | `mechanics/titan/parts/operator-console-helper-contracts/VALIDATION.md` |
| Titan appserver bridge docs, schemas, examples, script, and test | `mechanics/titan/parts/appserver-bridge-helper-contracts/` | `titan/appserver-bridge-helper-contracts` | moved | `mechanics/titan/parts/appserver-bridge-helper-contracts/VALIDATION.md` |
| Titan memory loom, recall, retention, and memory record docs, schemas, examples, script, and test | `mechanics/titan/parts/memory-loom-recall-helper-contracts/` | `titan/memory-loom-recall-helper-contracts` | moved | `mechanics/titan/parts/memory-loom-recall-helper-contracts/VALIDATION.md` |
| Titan visible session replay, phase graph, packet, compaction source, and learning delta docs, schemas, example, script, and test | `mechanics/titan/parts/session-praxis-replay-helper-contracts/` | `titan/session-praxis-replay-helper-contracts` | moved | `mechanics/titan/parts/session-praxis-replay-helper-contracts/VALIDATION.md` |
| Titan swarm task, report, finding, grade, timeout, ledger, and closeout docs, schemas, examples, script, and tests | `mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/` | `titan/swarm-ledger-closeout-helper-contracts` | moved | `mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/VALIDATION.md` |
| `schemas/change_signal.schema.json` | `mechanics/recurrence/parts/component-manifest-gate/schemas/change_signal.schema.json` | `recurrence/component-manifest-gate` | moved | `mechanics/recurrence/parts/component-manifest-gate/VALIDATION.md` |
| recurrence control plane, hardening, seed route, component templates, scan reports, local component manifests, manifest schemas, validator, and manifest tests | `mechanics/recurrence/parts/component-manifest-gate/` | `recurrence/component-manifest-gate` | moved | `mechanics/recurrence/parts/component-manifest-gate/VALIDATION.md` |
| recurrence hook pack docs, hook binding/run schemas, hook examples, hook manifests, and hook tests | `mechanics/recurrence/parts/hook-observation-pack/` | `recurrence/hook-observation-pack` | moved | `mechanics/recurrence/parts/hook-observation-pack/VALIDATION.md` |
| `docs/TECHNIQUE_PUBLICATION_HOOKS.md` | `mechanics/recurrence/parts/hook-observation-pack/docs/technique-publication-observation-boundary.md` | `recurrence/hook-observation-pack` | moved | `mechanics/recurrence/parts/hook-observation-pack/VALIDATION.md` |
| recurrence graph closure docs, graph snapshot/closure/delta schemas, examples, graph script, and graph tests | `mechanics/recurrence/parts/graph-closure-snapshot/` | `recurrence/graph-closure-snapshot` | moved | `mechanics/recurrence/parts/graph-closure-snapshot/VALIDATION.md` |
| recurrence live observation docs, live observation run schema, examples, collector script, and producer tests | `mechanics/recurrence/parts/live-observation-producers/` | `recurrence/live-observation-producers` | moved | `mechanics/recurrence/parts/live-observation-producers/VALIDATION.md` |
| recurrence beacon docs, observation/beacon/candidate-ledger schemas, examples, and beacon tests | `mechanics/recurrence/parts/beacon-candidate-pressure/` | `recurrence/beacon-candidate-pressure` | moved | `mechanics/recurrence/parts/beacon-candidate-pressure/VALIDATION.md` |
| recurrence review queue, dossier, owner summary, usage-gap schemas, examples, docs, and review-surface tests | `mechanics/recurrence/parts/owner-review-surface/` | `recurrence/owner-review-surface` | moved | `mechanics/recurrence/parts/owner-review-surface/VALIDATION.md` |
| recurrence owner-review decision docs, decision/closure/ledger/suppression schemas, examples, script, and closure tests | `mechanics/recurrence/parts/review-decision-closure/` | `recurrence/review-decision-closure` | moved | `mechanics/recurrence/parts/review-decision-closure/VALIDATION.md` |
| recurrence downstream projection docs, routing/stats/KAG/bundle/guard schemas, examples, script, and projection tests | `mechanics/recurrence/parts/downstream-projection-guard/` | `recurrence/downstream-projection-guard` | moved | `mechanics/recurrence/parts/downstream-projection-guard/VALIDATION.md` |
| recurrence wiring, connectivity, rollout, propagation, return handoff docs, schemas, examples, templates, and wiring tests | `mechanics/recurrence/parts/wiring-rollout-handoff/` | `recurrence/wiring-rollout-handoff` | moved | `mechanics/recurrence/parts/wiring-rollout-handoff/VALIDATION.md` |
| recurrence recursor readiness docs, schemas, examples, component manifest, script, and tests | `mechanics/recurrence/parts/recursor-readiness/` | `recurrence/recursor-readiness` | moved | `mechanics/recurrence/parts/recursor-readiness/VALIDATION.md` |
| detailed `docs/RELEASING.md` runbook payload and `tests/test_release.py` | `mechanics/release-support/parts/release-audit-publish-helper/` | `release-support/release-audit-publish-helper` | moved; root `docs/RELEASING.md` remains a preflight route door | `mechanics/release-support/parts/release-audit-publish-helper/VALIDATION.md` |
| detailed `docs/RELEASE_CI_POSTURE.md` posture payload | `mechanics/release-support/parts/public-support-ci-posture/` | `release-support/public-support-ci-posture` | moved; root `docs/RELEASE_CI_POSTURE.md` remains a public route door | `mechanics/release-support/parts/public-support-ci-posture/VALIDATION.md` |
| `tests/test_roadmap_parity.py` | `mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py` | `release-support/public-support-ci-posture` | moved | `mechanics/release-support/parts/public-support-ci-posture/VALIDATION.md` |
| `scripts/run_sibling_canary.py`, `scripts/sibling_canary_matrix.json`, and `tests/test_sibling_canary.py` | `mechanics/release-support/parts/public-support-ci-posture/` | `release-support/public-support-ci-posture` | moved; sibling canary is Tier 3 public-support CI drift detection, not a generic root script | `mechanics/release-support/parts/public-support-ci-posture/VALIDATION.md` |
| antifragility control-plane stress dispatch doc, request/decision examples, and public-surface test | `mechanics/antifragility/parts/stress-posture-dispatch-gate/` | `antifragility/stress-posture-dispatch-gate` | moved | `mechanics/antifragility/parts/stress-posture-dispatch-gate/VALIDATION.md` |
| antifragility closeout stress carry doc, reviewed manifest example, and carry test | `mechanics/antifragility/parts/reviewed-stress-closeout-carry/` | `antifragility/reviewed-stress-closeout-carry` | moved | `mechanics/antifragility/parts/reviewed-stress-closeout-carry/VALIDATION.md` |
| antifragility via negativa checklist and pruning test | `mechanics/antifragility/parts/via-negativa/` | `antifragility/via-negativa` | moved | `mechanics/antifragility/parts/via-negativa/VALIDATION.md` |
| RPG SDK addendum doc and API regression test | `mechanics/rpg/parts/typed-consumer-api/` | `rpg/typed-consumer-api` | moved | `mechanics/rpg/parts/typed-consumer-api/VALIDATION.md` |
| RPG surface path doc and route test | `mechanics/rpg/parts/surface-path-transport/` | `rpg/surface-path-transport` | moved | `mechanics/rpg/parts/surface-path-transport/VALIDATION.md` |

## Next Audit Route

After every payload move, inspect root districts for remaining single-mechanic
files, update `mechanics/topology.json`, repair links and generated refs, run
the part-local checks, then run the mechanics topology gate.
