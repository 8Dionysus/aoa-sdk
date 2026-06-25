# Changelog

All notable changes to `aoa-sdk` will be documented in this file.

The format is intentionally simple and human-first.
Tracking starts with the community-docs baseline for this repository.

## [Unreleased]

### Summary

- Align the local `evals/` port with the root README and design anatomy maps
  so SDK-local eval pressure is discoverable while proof authority remains in
  `aoa-evals`.
- Add an OS Abyss artifact bundle gate for built `aoa-sdk` wheel/sdist outputs,
  producing ABI, SBOM, SLSA/in-toto, signature-decision, and verify sidecars
  under ignored `dist/abyss-artifact-bundle/` before release artifacts upload.
- Add typed SDK loading for OS Abyss artifact producer-profile read models so
  agents can inspect owner repos, artifact classes, validator commands, sidecars,
  trust-root modes, and consumer expectations without treating the SDK as host
  enforcement authority.

### Notes

- Add future changes here after the release tag lands. Dated release sections
  own exact reconciliation spans and validation evidence.

## [0.4.0] - 2026-06-06

### Summary

- `v0.4.0` closes the measured `v0.2.3..origin/main` release-prep span:
  52 first-parent commits before the version commit, 1398 changed paths,
  landed PRs through `#165`, 66 decision records, and 12 active mechanics
  packages. The largest changed surfaces were `mechanics/` (824 paths),
  `.agents/` portable skill exports (235), `src/` (133), `docs/` (90),
  `tests/` (35), `sdk/` (24), `quests/` (19), `scripts/` (11), and
  `generated/` (8).
- `aoa-sdk` now has the same explicit rationale/design spine expected from
  the refactored AoA repositories: decisions explain why, design surfaces
  explain system and agent-facing form, generated indexes stay derived, and
  root documents stay route-focused.
- `aoa-sdk` now has a corrected mechanics topology after sibling-source
  reread: package cards route 12 active mechanics packages, SDK-specific lanes
  stay as parts, and the first Agon recurrence-adapter payload now lives in
  its functioning part-local home.
- `aoa-sdk` now has a checked `sdk/` source-home tree for SDK-owned posture:
  public interface, facade boundary, runtime entry, and distribution routes.
  `src/aoa_sdk/` remains the importable Python implementation and
  `mechanics/` remains the repeatable operation topology.
- Mechanics future pressure now has its own roadmap layer:
  `mechanics/ROADMAP.md` routes mechanics-wide pressure, each active package
  has a package `ROADMAP.md`, and the mechanics topology validator requires
  those surfaces. Package roadmaps now follow the center mechanic form:
  current contour, next work, condition-based future movement, and stop lines
  instead of repeated update-trigger tails.
- Checkpoint implementation topology now has its first tree-shaped cut:
  checkpoint filesystem path naming lives in
  `src/aoa_sdk/checkpoints/topology/paths.py`, while `registry.py` remains the
  behavioral `CheckpointsAPI` facade.
- `src/aoa_sdk` now has a generated source-topology index at
  `generated/source_topology.min.json` so agents can inspect implementation
  route keys, split pressure, and next-route hints before loading large modules.
- Checkpoint implementation helpers now live in route-role branches for
  runtime sessions, hook/git boundaries, reviewed promotion targets, rendering,
  after-commit review, agent-review carry, note ledger assembly, and reviewed
  closeout bridge support. `CheckpointsAPI` remains the public facade.
- Checkpoint lifecycle now has an explicit audit and close/archive route:
  `current/` is measured as active-now or still-blocked review work, reviewed
  closeout execution can be closed append-only and archived, stale scopes can
  move as archive evidence, and aoa-session-memory stays read-only evidence.
- Checkpoint session reconciliation now covers Codex sessions closed without
  reviewed closeout: `reconcile-sessions` / `sweep-closed-sessions` dry-run by
  default, read aoa-session-memory refs without mutating them, archive
  nonpending no-closeout scopes with `archived_without_closeout`, and write a
  generated lifecycle navigation index with graph-ready anchors.
- Checkpoint backlog audit now exposes the open no-closeout and stale-current
  pressure before movement: runtime trace refs, session-memory archive status,
  raw refs, required actions, next routes, and a generated backlog navigation
  index stay read-only and below memory, proof, closeout, owner, RAG, and
  GraphRAG authority.
- Checkpoint candidate intelligence now derives action facets, action
  signatures, repetition clusters, wrapper-gap candidates, existing-wrapper
  fit, wrapper readiness, bounded sample-audit targets, and a generated
  navigation index. It can surface skill, playbook, technique, eval, memo,
  SDK-local checkpoint mechanic, owner-local, and unknown wrapper pressure
  without promoting a single event or accepting wrapper truth.
- Checkpoint candidate intelligence also re-enriches legacy saved action
  signatures from their action events and saved event refs, so old checkpoint
  notes gain event-type, route-signal, mutation, authority, provenance, and
  repeat-count-aware negative-evidence axes without rewriting the note.
- Checkpoint carrier intelligence now separates ecosystem carrier candidates
  from wrapper-family hints. It can surface mechanic, tool, MCP, hook, script,
  daemon, service, index, and unknown carrier pressure with owner scope,
  execution risk, installability, generated navigation, and sample-audit lanes,
  while keeping `sdk_local` private to SDK checkpoint scope and blocking hidden
  install, registration, execution, RAG/GraphRAG, memory, proof, or owner
  authority.
- Checkpoint reviewed closeout support now has pipeline branches for
  followthrough decisions, context/session scope, evidence reading, mechanical
  artifact execution, and owner handoff. `closeout/bridge.py` is a thin
  compatibility facade, and checkpoint closeout remains below durable memory,
  proof, progression, quest, and owner-approval truth.
- Surface detection now has route-role implementation branches for opportunity
  item derivation, context and receipt enrichment, checkpoint candidate
  clusters, progression-axis signals, and reviewed closeout handoff assembly.
  `surfaces/registry.py` remains the public `SurfacesAPI` facade and
  owner-layer signal hints stay advisory.
- Agon helper payloads and the Experience capture helper seam now live
  in active part-local homes with role, input, output, owner, next-route, and
  validation cards instead of root technical districts.
- Remaining Experience helper contract bundles now live in active
  `mechanics/experience/parts/` homes named by route role instead of by old
  chronological tests or root API docs: adoption federation, deployment/watchtower,
  governance runtime, and office release-train helper contracts.
- Titan helper contract bundles now live in active `mechanics/titan/parts/`
  homes with route names for incarnation/runtime, operator console, appserver
  bridge, memory/recall, visible-session replay, and swarm closeout.
- Recurrence root payload now lives under active part-local homes: component
  manifest gate, hook observation pack, graph closure snapshot, live observation
  producers, beacon candidate pressure, owner review surfaces, review decision
  closure, downstream projection guards, wiring/rollout handoff, and recursor
  readiness. Part names describe route role instead of old chronological or insert
  receipts.
- Boundary Bridge owner-layer signal handoff and Checkpoint child-task reentry
  payload now live in part-local homes. Active docs, examples, tests, fixture
  IDs, and A2A helper names use route-role vocabulary instead of chronological
  labels.
- Antifragility root payload now lives in part-local homes for
  stress-posture dispatch gating, reviewed stress closeout carry, and via
  negativa pruning. Active paths now name the request, decision, manifest
  carry, checklist, owner route, and validation instead of root doc titles.
- RPG root docs and API tests now live in part-local homes for typed consumer
  API and surface-path transport, while `src/aoa_sdk/rpg/` remains the
  importable SDK source home.
- Checkpoint reviewed closeout context carry now lives in the
  `mechanics/checkpoint/parts/reviewed-closeout-context-carry/` part. Active
  docs, schemas, examples, and tests name advisory carry routes for owner
  followthrough, component refresh, continuity, and next-kernel decisions
  instead of old root filenames.
- Boundary Bridge skill runtime bridge docs and tests now live in
  `mechanics/boundary-bridge/parts/skill-runtime-bridge/`, where active names
  describe recommendation actionability and host reporting instead of old
  root gap/spec filenames.
- Release Support detailed runbook, public support/CI posture, and release
  helper tests now live in part-local homes for release audit/publish helpers
  and public support CI posture. Root release docs remain thin active route
  doors for federation preflight and public onboarding.
- Codex Projection workspace MCP server docs, runnable script, and tests now
  live in `mechanics/codex-projection/parts/workspace-mcp-server/`. The active
  route names the MCP server operation, while `src/aoa_sdk/codex/workspace_mcp.py`
  remains the importable SDK source home.
- Technique publication hook guidance now lives under the Recurrence
  `hook-observation-pack` as a technique publication observation boundary. The
  active route names observation-only behavior instead of implying runtime
  technique hooks.
- Boundary Bridge now has a `technique-promotion-readiness-reader` part for the
  `aoa-techniques` facade regression. The test moved out of root `tests/` while
  `src/aoa_sdk/techniques/` remains the importable SDK source home.
- Checkpoint reviewed session handoff runner docs, operator scripts, and
  closeout inbox user unit templates now live under the
  `mechanics/checkpoint/parts/reviewed-session-handoff-runner/` route and
  point at the part-local inbox processor.
- Checkpoint session-growth capture and reviewed checkpoint-note promotion docs
  now live in `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/`,
  with generated workspace control-plane refs pointing at the part-local cycle
  docs.
- Checkpoint managed Git hook templates now live under
  `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/`,
  so hook filenames stay Git-native while the active route names the owning
  operation.
- Root technical districts are now guarded by an explicit mechanics topology
  allowlist: root remains for public, repo-wide, generated, schema, tooling,
  and fixture contracts, while new single-mechanic payload must use
  topologically named part-local mechanics homes.
- The SDK remains a bounded typed control plane for sibling-owned surfaces. It
  can discover, validate, inspect, and hand off source-owned artifacts, but it
  still does not own routing truth, skill execution meaning, proof verdicts,
  durable memory truth, role authority, playbook law, stats state, KAG
  meaning, or runtime behavior.

### Reconciliation Basis

- This release section was reconstructed from
  `git log --first-parent v0.2.3..origin/main`, `git diff --name-status`,
  merged PR metadata, landed decision records, route cards, compatibility
  policy, workspace fixtures, mechanics topology, source topology, and the
  current release gate rather than from the moving changelog contour alone.
- Future `Unreleased` entries should record stable route, owner, and
  validation changes without live first-parent commit totals, changed-path
  totals, PR ranges, or remote check handles; dated release sections own exact
  reconciliation.
- The largest current topology change is not a package version bump. It is the
  shift from implicit root prose and stale sibling paths toward explicit
  owner-surface routing, decision rationale, design law, and canonical sibling
  compatibility paths.

### Final Route Sweep

- Root entry now routes structural questions through `DESIGN.md`,
  agent-facing guidance questions through `DESIGN.AGENTS.md`, and rationale
  changes through `docs/decisions/README.md`.
- Decision records now live under canonical `AOA-SDK-D-####` filenames with
  generated lookup indexes by number, date, surface, SDK facet, mechanic
  parent, and guard family.
- Mechanics now live under `mechanics/` as operation topology with
  source-surface provenance, candidate parts, functioning part-local artifact
  homes, package-local route cards, and a dedicated topology validator.
- Former over-specific parent candidates now live only in package-local
  legacy indexes. Active mechanics use topological part names such as
  `workspace-root-resolution`, `consumed-surface-posture-gate`,
  `owner-layer-signal-handoff`, `reviewed-session-handoff-runner`,
  `child-task-reentry`, and `live-rollout-status-readout`.
- Compatibility policy now follows refactored sibling owner paths for
  `aoa-memo` memory, memory-object, checkpoint-to-memory, runtime-writeback,
  and `aoa-evals` runtime-candidate surfaces instead of treating old
  root-level generated paths as active routes.
- Test workspace fixtures, KAG handoff/regrounding refs, playbook federation
  refs, and sample review packet refs now point at those canonical owner
  paths so tests exercise current topology.

### Control-Plane Authority And Boundary

- `src/aoa_sdk/` stays the importable SDK source home; a future top-level
  `sdk/` district is not added merely to mirror the package name.
- `mechanics/` packages name repeatable SDK operations. Functioning parts may
  own single-mechanic config, docs, schemas, generated companions, scripts,
  tests, and helper contracts, while root `quests/` owns source quest records,
  `src/aoa_sdk/` remains the importable SDK source home, and sibling source
  truth stays outside the SDK.
- Local compatibility repairs should move the canonical path to the stronger
  owner-local path. Hidden compatibility fallback is not a substitute for
  acknowledging sibling topology drift.

### Added

- Root `DESIGN.md` as the SDK system-form surface for source homes, generated
  companions, control-plane boundaries, and the mechanics split.
- Root `DESIGN.AGENTS.md` as the agent-facing design surface for route-card
  shape, validation posture, closeout expectations, and future local guidance
  growth.
- `docs/decisions/` as the canonical rationale lane, including template,
  local `AGENTS.md`, index contract, generated read models, release-check
  wiring, and initial decisions for decisions-before-mechanics,
  design-before-mechanics, and refactored sibling surface paths.
- `mechanics/` as the SDK initial operation topology with root and
  package-local `AGENTS.md`, `README.md`, `PARTS.md`, `PROVENANCE.md`,
  `topology.json`, a validator, and regression tests.
- `mechanics/ROADMAP.md` plus package `ROADMAP.md` files as the mechanics
  future-pressure router and package-local future-contour layer.
- `mechanics/agon/parts/recurrence-adapter/` as the first functioning
  part-local payload home, including local config, docs, schemas, generated
  registries, builders, validators, and tests; Questbook source records route
  through root `quests/`.
- Agon functioning helper parts for center-law previews, state-packet review
  bindings, duel-kernel review bindings, verdict/retention/rank review
  helpers, epistemic/KAG review helpers, SLC review helpers, and Sophian
  threshold review helpers.
- `mechanics/experience/parts/capture-pipeline-helper/` as the active home for
  the Experience capture/pipeline helper contract.
- `AOA-SDK-D-0005` as the parent-boundary correction decision, superseding the
  first topology draft's parent package set.
- `AOA-SDK-D-0006` as the source-family crosswalk decision, making every
  `src/aoa_sdk/*` family route through a parent mechanic without promoting
  module names into parents.
- Regression coverage for decision-index freshness, design-route presence,
  canonical sibling compatibility paths, and memo source-file path selection.
- Mechanics topology validation now checks live `src/aoa_sdk/*` source-family
  coverage in addition to the parent package set and demoted parent candidates.
- Mechanics topology validation now checks functioning part directories for
  local `README.md`, `CONTRACT.md`, and `VALIDATION.md` surfaces.
- `AOA-SDK-D-0008`, `AOA-SDK-D-0009`, `AOA-SDK-D-0010`, and `AOA-SDK-D-0011`
  record Codex Projection, Agon helper, Experience helper, and Titan helper
  artifact localization decisions.
- `AOA-SDK-D-0013` records Boundary Bridge owner-layer signal handoff and
  Checkpoint child-task reentry localization, including active API naming away
  from chronological helper names.
- `AOA-SDK-D-0014` records Antifragility active part localization for
  stress-posture dispatch gating, reviewed stress closeout carry, and via
  negativa pruning.
- `AOA-SDK-D-0015` records RPG typed consumer API and surface-path transport
  localization.
- `AOA-SDK-D-0016` through `AOA-SDK-D-0030` record the remaining active
  mechanics localization landings: Checkpoint closeout carry, skill runtime
  bridge, Release Support, Codex workspace MCP, technique observation and
  promotion readers, reviewed-session handoff, session-growth checkpoint
  cycle, localized tests, recurrence change-signal schema, and Checkpoint
  local automation templates.
- `AOA-SDK-D-0031` records sibling-canary localization under the
  public-support CI posture part.
- `AOA-SDK-D-0032` records root technical district route-card hardening for
  docs, scripts, tests, and checked-in skill exports.
- `AOA-SDK-D-0033` records the now-superseded Questbook parent withdrawal that
  treated root quest records as Agon part-local payload.
- `AOA-SDK-D-0034` records active mechanics topology status naming after
  localization completed and stale partial/topology-draft vocabulary left the active
  surface.
- `AOA-SDK-D-0035` records `abyss-stack` diagnostic catalog compatibility
  canonicalization: the SDK now uses the diagnostic-spine part-local path
  without an old root generated fallback.
- `AOA-SDK-D-0036` records root technical district allowlist validation, making
  root additions fail topology validation unless they are explicit root
  contracts or moved into topologically named part-local mechanics homes.
- `AOA-SDK-D-0037` records workspace MCP surface-crosswalk naming: secondary
  orientation routes now use `secondary_surface` instead of an active
  `fallback` field.
- `AOA-SDK-D-0038` records manual-equivalence lane naming for router-only skill
  recommendations: active outputs now use `manual-equivalence` and
  `manual_equivalence_*`, with old fallback field names accepted only as input
  aliases.
- `AOA-SDK-D-0039` records A2A quest-passport secondary-tier naming, replacing
  the SDK-owned `fallback_tier` output field with `secondary_tier`.
- `AOA-SDK-D-0040` records sibling fallback-key input alias normalization:
  SDK models now expose route-bearing `secondary_actions` and `recovery_mode`
  fields while accepting old sibling keys only as validation aliases.
- `AOA-SDK-D-0041` records external stress fallback-ref accounting:
  fallback-shaped stress refs may remain exact only as source/routing evidence handles,
  not as SDK-owned active route names.
- `AOA-SDK-D-0042` supersedes the Questbook parent withdrawal and restores
  root `quests/` as the lane/state source quest record district with
  `mechanics/questbook/` as active source-store and lifecycle posture.
- `AOA-SDK-D-0046` records the changelog volatility boundary: live
  `Unreleased` entries stay free of commit totals, changed-path totals, PR
  ranges, and remote check handles, while dated release sections own exact
  reconciliation spans.
- `AOA-SDK-D-0047` records the docs-map cleanup: `docs/README.md` is now the
  docs entry map, stale flat docs are retired, and decision lookup routes
  through generated indexes instead of a manual latest-decision roster.
- `AOA-SDK-D-0048` records the root roadmap direction-surface split: roadmap
  owns direction, horizons, and future triggers while changelog, mechanics,
  generated companions, and decision indexes own detailed inventories.
- `AOA-SDK-D-0061` records the checkpoint lifecycle close/archive route,
  including pending-review blocking, append-only lifecycle closure, stale
  archive evidence, and the read-only aoa-session-memory boundary.

### Changed

- Root `AGENTS.md`, `README.md`, `ROADMAP.md`, and `docs/boundaries.md` now
  route structural, design, and decision questions to their owning surfaces
  instead of carrying the full explanation inline.
- Root `README.md` is now a command-free public front door. Executable
  validation routes stay in `AGENTS.md`, nearest nested route cards, part
  `VALIDATION.md`, release docs, and owning tests; `AOA-SDK-D-0045` records
  the route-law decision.
- Root `README.md` now matches the repository `LICENSE` and package metadata
  by naming Apache License 2.0 instead of MIT.
- Root docs now route through `docs/README.md` as a documentation map instead
  of relying on a flat `docs/` shelf.
- `docs/decisions/README.md` now points to generated lookup indexes instead of
  hand-maintaining the active mechanics decision roster.
- Root `ROADMAP.md` now follows an authority/update-rule/horizon shape and no
  longer hand-maintains a part-local shipped-surface inventory.
- `DESIGN.md` and `DESIGN.AGENTS.md` now route single-mechanic local
  automation templates through part-local mechanics homes instead of former
  root local-automation districts.
- Mechanics package cards now use a consistent active-topology status instead
  of stale draft-topology labels after part-local payload localization.
- `mechanics/topology.json` now names the current state
  `active-part-localized-topology` with complete payload movement, and the
  topology validator rejects stale in-progress status names or migration
  vocabulary inside active route IDs.
- `ROADMAP.md`, `DESIGN.md`, `DESIGN.AGENTS.md`, root district route cards,
  and mechanics part cards now describe current routes and alternate-path
  behavior without stale draft-topology or fallback route wording in active prose.
- Root `docs/`, `scripts/`, `tests/`, and `.agents/skills/` now have local
  route cards registered in the nested AGENTS validator so single-mechanic
  payload has a nearest stop-line before it lands in root.
- Root `quests/` is restored as a Questbook source-record district, not a
  generic payload lane; Agon helper notes now live in `quests/agon/ready/`
  while helper contracts remain in `mechanics/agon/parts/*`.
- `sdk/` is now a checked source-home tree, with route cards and manifest
  coverage for public-interface, facade-boundary, runtime-entry, and
  distribution posture.
- `scripts/validate_sdk_source_home.py` now validates the SDK source-home
  manifest, branch cards, family README routes, route targets, and absence of
  mechanic `PARTS.md` vocabulary under `sdk/`.
- `scripts/release_check.py` now checks generated decision indexes before the
  rest of the release gate.
- `scripts/release_check.py` now checks SDK source-home and mechanics topology
  before the rest of the release gate.
- `scripts/validate_nested_agents.py` recognizes `DESIGN.AGENTS.md` as an
  active agent-facing guidance surface.
- `scripts/validate_nested_agents.py` now tracks the Agon parts route card as
  an active nested guidance surface.
- `scripts/validate_nested_agents.py` now tracks the part-local Checkpoint
  `git-boundary-hook-templates/` and `closeout-inbox-user-units/` route cards
  instead of root local automation districts.
- `src/aoa_sdk/codex/workspace_mcp.py` and `src/aoa_sdk/routing/picker.py`
  now route memo catalog inspection to the refactored `generated/memory/`
  surface.
- `src/aoa_sdk/compatibility/policy.py` now uses canonical refactored paths
  for migrated memo and eval surfaces while preserving stable SDK surface IDs.
- `src/aoa_sdk/compatibility/policy.py` now requires the `abyss-stack`
  diagnostic-spine part-local catalog and no longer treats the old root
  generated diagnostic catalog as an active compatibility fallback.
- `src/aoa_sdk/codex/workspace_mcp.py` reports whether project-level
  `aoa_workspace` MCP config points at the part-local server script.
- `src/aoa_sdk/codex/workspace_mcp.py` now reports the `abyss-stack`
  diagnostic catalog runtime entrypoint through the part-local diagnostic-spine
  path.
- `scripts/validate_mechanics_topology.py` now validates root technical
  districts against an explicit allowlist and rejects re-created root
  `config/`, `examples/`, `manifests/`, `githooks/`, and `systemd/` districts
  unless a root contract deliberately reopens them; root `quests/` is
  allowlisted only as the Questbook source-record district.
- `src/aoa_sdk/codex/workspace_mcp.py` now exposes
  `surface-crosswalk.secondary_surface` and asks prompts for a secondary
  surface rather than a fallback route.
- `src/aoa_sdk/models.py`, `src/aoa_sdk/skills/detector.py`,
  `src/aoa_sdk/surfaces/registry.py`, and `src/aoa_sdk/cli/main.py` now name
  router-only skill preservation as manual equivalence instead of an active
  manual-fallback lane.
- `src/aoa_sdk/a2a/rebase/models.py` now emits `QuestPassport.secondary_tier`
  for optional delegation planning instead of `fallback_tier`.
- `src/aoa_sdk/models.py` now exposes sibling routing/playbook posture as
  `secondary_actions` and `recovery_mode` while keeping `fallback_actions` and
  `fallback_mode` as input-only aliases for current sibling generated JSON.
- `src/aoa_sdk/checkpoints/registry.py` now names local timestamp synthesis as
  a defaulting helper instead of a fallback helper.
- `src/aoa_sdk/checkpoints/lifecycle.py` now owns checkpoint lifecycle audit
  and close/archive orchestration, while `registry.py` remains the
  `CheckpointsAPI` facade.
- Live workspace runtime-mirror tests now validate `aoa-skills` outer-ring
  count and readiness consistency from the owner surface instead of pinning the
  older 10-skill contour; the live preflight check observed the owner surface
  expanded to 14 skills.
- Release-support runbook and public CI posture commands now use the live
  workspace root `/srv/AbyssOS` for release audit and publish commands.
- Routing owner-layer shortlist parsing now accepts `source_route` hints from
  `aoa-routing`, preserving them as advisory owner-layer routing evidence
  without turning them into SDK-owned executable surfaces.
- Checkpoint part docs now define `current/` as active runtime or still
  actionable checkpoint state, not as a long-lived archive of old runtime
  scopes.
- `src/aoa_sdk/recurrence/live_observations.py` now detects repeated
  alternate-path pressure with active alternate-path vocabulary.
- Antifragility stress contracts now state that `retrieval-only-fallback`
  strings in examples are external source/routing evidence handles, while new
  SDK-owned stress posture names must use degraded, recovery, source-first, or
  alternate-path vocabulary.

### Moved Or Retired

- Agon recurrence-adapter and prebinding review-lane config, docs, schemas,
  generated registries, builders, validators, and tests moved from root
  technical districts into `mechanics/agon/parts/recurrence-adapter/`; their
  quest source records are restored in `quests/agon/ready/`.
- Remaining Agon helper config, docs, schemas, examples, generated registries,
  builders, validators, and tests moved from root technical districts into
  their owning `mechanics/agon/parts/*/` routes; their quest source records
  are restored in `quests/agon/ready/`.
- Experience capture/pipeline helper docs, schema, example, and test
  moved from root technical districts into
  `mechanics/experience/parts/capture-pipeline-helper/`.
- Remaining Experience adoption/federation, deployment/watchtower, governance
  runtime, and office release-train docs, schemas, examples, and seed contract
  tests moved from root technical districts into their owning
  `mechanics/experience/parts/*/` routes.
- Titan docs, schemas, examples, scripts, and tests moved from root technical
  districts into their owning `mechanics/titan/parts/*/` routes while
  `src/aoa_sdk/titans/` remains the importable SDK source home.
- Owner-layer surface detection docs and tests moved from root `docs/` and
  `tests/` into
  `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/`.
- A2A summon/return/checkpoint docs, examples, and tests moved from root
  `docs/`, `examples/a2a/`, and `tests/` into
  `mechanics/checkpoint/parts/child-task-reentry/`; active runtime closeout
  helper vocabulary now uses return-checkpoint names instead of chronological
  names.
- Antifragility control-plane docs, closeout carry docs, via negativa
  checklist, stress examples, closeout manifest example, and public-surface
  regression moved from root `docs/`, `tests/fixtures/antifragility/`, and
  `tests/` into `mechanics/antifragility/parts/*/` route homes.
- RPG SDK addendum, surface path docs, and RPG API regression test moved from
  root `docs/` and `tests/` into `mechanics/rpg/parts/*/` route homes.
- Test fixtures for `aoa-memo` memory readers moved from root-level
  `generated/` into `generated/memory/` and `generated/memory-objects/`.
- Test fixtures for `aoa-memo` checkpoint and runtime-writeback surfaces moved
  into their mechanics part-local homes under `mechanics/checkpoint/parts/`
  and `mechanics/writeback/parts/`.
- Test fixtures for `aoa-evals` runtime-candidate readers moved into the
  audit mechanic's `candidate-readers` part-local generated lane.
- Codex workspace MCP docs, server script, and tests moved from root `docs/`,
  `scripts/`, and `tests/` into
  `mechanics/codex-projection/parts/workspace-mcp-server/`.
- Technique publication hook guidance moved from root `docs/` into
  `mechanics/recurrence/parts/hook-observation-pack/docs/`.
- Technique promotion-readiness facade regression moved from root `tests/` into
  `mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/tests/`.
- Reviewed session handoff runner docs and closeout inbox installer/processor
  scripts moved from root `docs/` and `scripts/` into
  `mechanics/checkpoint/parts/reviewed-session-handoff-runner/`.
- Session-growth checkpoint cycle docs moved from root `docs/` into
  `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/`.
- Managed Checkpoint Git hook templates moved from root `githooks/` into
  `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/`.
- Closeout inbox user unit templates moved from root `systemd/` into
  `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/`.
- Sibling canary script, matrix, and regression moved from root `scripts/` and
  `tests/` into
  `mechanics/release-support/parts/public-support-ci-posture/`.
- `mechanics/TOPOLOGY_PREP.md` and `mechanics/ARTIFACT_TOPOLOGY.md` were
  retired from the active mechanics root. Current mechanics work routes
  through `mechanics/README.md`, `mechanics/topology.json`, package
  `PROVENANCE.md`, and part `VALIDATION.md`.
- `docs/AGENTS_ROOT_REFERENCE.md` and `docs/ecosystem-impact.md` were retired
  from active `docs/`; current root guidance and ecosystem posture now route
  through active owner surfaces.
- Old root-level migrated memo/eval paths are retired from active SDK
  compatibility for these surfaces; workspaces exposing only those paths now
  fail compatibility as topology drift.

### Validation

- `python scripts/generate_decision_indexes.py --check`
- `python scripts/validate_sdk_source_home.py`
- `python scripts/validate_mechanics_topology.py`
- `python scripts/build_workspace_control_plane.py --check`
- `python scripts/validate_workspace_control_plane.py`
- `python -m pytest -q`
- `python -m ruff check .`
- `python -m mypy src`
- `python -m build`
- `aoa compatibility check /srv/AbyssOS/aoa-sdk`
- `aoa checkpoint lifecycle-audit /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json`
- `aoa checkpoint close-archive /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json`
- `python scripts/release_check.py`
- `aoa release audit /srv/AbyssOS --phase preflight --repo aoa-sdk --strict --json`

### Notes

- This dated section is the canonical `v0.4.0` reconciliation contour. It was
  built from changelog history plus git, PR, decision, topology, live
  workspace, and release-audit evidence.
- GitHub publication remains authoritative only after the annotated `v0.4.0`
  tag and GitHub Release are created from this section and postpublish audit
  passes.
- The May 31 canonical-path landing intentionally rejected hidden fallback for
  migrated `aoa-memo` and `aoa-evals` surfaces.

## [0.2.3] - 2026-04-23

### Summary

- this patch expands the SDK control plane across Agon recurrence lanes,
  helper candidates, state-packet bindings, verdict-delta and sealed-commit
  helpers, duel-kernel bindings, mechanical-trial helpers, retention-rank
  helpers, KAG/Sophian helper surfaces, and typed Experience adoption APIs
- recurrence projections, reviewed-closeout carry, stats re-grounding,
  recursor readiness, Titan runtime harnesses, Titan incarnation CLI support,
  and Experience capture/deployment/watchtower/release helper contracts are
  hardened
- `aoa-sdk` remains a bounded typed access and orchestration layer for
  sibling-owned surfaces rather than a source-owning runtime or doctrine repo

### Added

- Agon recurrence adapter registry, prebinding review lanes, state-packet
  SDK bridges, verdict-delta and sealed-commit helper candidates, duel-kernel
  SDK bindings, mechanical-trial helpers, retention-rank helpers,
  KAG/Sophian helpers, and epistemic review SDK helper surfaces
- recurrence control-plane seeds, graph/manifest compatibility inserts,
  downstream projections, live-observation producers, recursor readiness
  helpers, stats re-grounding policy, and source-ref-aware routing inspection
- Titan runtime harness surfaces, Titan incarnation spine runtime support, and
  Titan CLI gate handling
- Experience capture pipeline helpers plus certification, deployment,
  federation, adoption, governance, watchtower, rollback, release, dashboard,
  and ToS dossier API contracts

### Changed

- SDK review follow-ups, recurrence projection schemas, helper imports,
  closeout follow-through capture, helper contract inputs, adoption typed
  coverage, API contract coverage, stats re-grounding behavior,
  and Titan CLI gate handling were tightened for the current control-plane
  release line

### Validation

- `python scripts/release_check.py`

### Notes

- this patch changes control-plane helper behavior and release metadata only;
  sibling repositories remain authoritative for their own objects, evidence,
  roles, runtime records, and doctrine

## [0.2.2] - 2026-04-19

### Summary

- this patch hardens checkpoint review and quarantine flow, recurrence
  control-plane surfaces, and A2A summon planning helpers across the SDK
- memo writeback intake, release workflow safety, and roadmap/repo-contract
  surfaces are tightened without widening `aoa-sdk` into a runtime owner
- `aoa-sdk` remains the bounded control plane for sibling-owned AoA surfaces

### Added

- recurrence control-plane and hook-producer surfaces plus A2A summon planning
  helpers and end-to-end fixtures
- checkpoint auto-review, review carry, and closeout follow-through fixes
  across the active session-ledger path

### Changed

- checkpoint typing, memo writeback intake, required-check plus Node24
  workflow refs, and release-facing repo posture are tightened for the current
  control-plane release line

### Validation

- `python scripts/release_check.py`

### Notes

- this patch stays on the control plane: checkpoint orchestration,
  recurrence, and summon helpers are tightened without turning `aoa-sdk` into
  a source-owning runtime layer

## [0.2.1] - 2026-04-12

### Summary

- this patch hardens Codex Projection live rollout status reads, rollout reference
  boundaries, and continuity carry in the control plane
- closeout follow-through and release publish failure handling are tightened
  without widening `aoa-sdk` into a runtime owner
- the release remains a bounded control-plane refinement over `v0.2.0`

### Added

- Codex Projection live rollout status surfaces and deploy-operation boundary guidance
  for the control plane.
- self-agency continuity carry and closeout follow-through mapping for
  checkpoint-driven rollout sessions.
- rollout campaign reference-boundary guidance so campaign refs stay explicit
  and local-first.

### Changed

- release-audit typing and live rollout status reads are hardened across the
  current Codex Projection rollout path.

### Fixed

- `aoa release publish` now treats GitHub Release lookup timeouts as an unknown remote state and aborts before tag mutation.
- checkpoint closeout execution now writes reports and reviewed artifacts into the same runtime-session-scoped ledger as the generated closeout context.

### Validation

- `python scripts/release_check.py`

### Notes

- this patch stays on the control plane: rollout references,
  continuity carry, and deploy-state reads are tightened without turning
  `aoa-sdk` into a source-owning runtime layer.

## [0.2.0] - 2026-04-10

### Summary

- this release adds a workspace control-plane capsule, first-class checkpoint lanes, closeout bridging, and thread-aware Codex session tracing
- checkpoint typing, registry guardrails, actor references, local-time reporting, and control-plane validation are hardened across CLI and generated outputs
- `aoa-sdk` remains the typed control-plane and orchestration layer rather than a runtime owner

### Validation

- `python scripts/release_check.py`

### Notes

- detailed source, schema, generated-surface, and operator-surface coverage for this release remains enumerated below under `Added`, `Changed`, and `Included in this release`

### Added

- workspace control-plane capsule plus compatibility tracking for center/root
  entry capsules and routing/stats ABI v2
- a first-class checkpoint lane with auto-captured skill-phase and
  commit-growth checkpoints, progression carry-through, and closeout execution
  bridging
- thread-aware Codex session tracing and runtime-identity scoping for
  checkpoint closeout

### Changed

- hardened checkpoint typing, registry guardrails, actor refs, and local-time
  reporting across CLI and generated outputs
- expanded docs, tests, and dev extras around checkpoint closeout and
  control-plane validation

### Included in this release

- control-plane and typed-consumer expansion across `src/`, `schemas/`,
  `generated/`, `scripts/`, and `systemd/`, including RPG and `aoa-stats`
  consumer slices, reviewed closeout submission flows, closeout publishers and
  watchers, surface detection, and the workspace control-plane capsule
- workspace, checkpoint, and operator surfaces across `docs/`, `README.md`,
  `AGENTS.md`, `.agents/`, `.github/`, `tests/`, and `pyproject.toml`,
  including portable bootstrap and ingress wrappers, foundation skill
  detection, via negativa and antifragility doctrine, and thread-aware
  checkpoint-closeout hardening

## [0.1.0] - 2026-04-01

First public baseline release of `aoa-sdk` as the typed Python SDK for the AoA federation.

This changelog entry uses the release-prep merge date.

### Summary

- first public baseline release of `aoa-sdk` as the local-first typed consumer and orchestration spine for source-owned AoA surfaces
- the live read path now covers `aoa-routing`, `aoa-skills`, `aoa-agents`, `aoa-playbooks`, `aoa-memo`, `aoa-evals`, and bounded `aoa-kag` inspect support
- the release also ships workspace discovery, source-checkout versus runtime-mirror topology handling, compatibility checks, skill session helpers, and CLI inspection surfaces

### Added

- seeded the repository from the initial `Dionysus` `aoa-sdk` starter artifacts
- the first package scaffold, boundary docs, workspace layout docs, versioning docs, and ecosystem impact docs
- the first live local-first read path to `aoa-routing`, `aoa-skills`, and `aoa-agents`
- sibling workspace discovery, typed surface loaders, skill session helpers, and isolated fixture-based tests
- the extended local-first read path to `aoa-playbooks`, `aoa-memo`, and `aoa-evals`
- an explicit per-surface compatibility policy, including versioned and versionless surface handling
- a tracked workspace manifest, environment overrides, and CLI inspection for source-checkout versus runtime-mirror topology

### Changed

- workspace discovery now prefers the git source checkout at `~/src/abyss-stack` over the deployed runtime mirror at `/srv/AbyssOS/abyss-stack`
- package and CLI version surfaces are now aligned to `0.1.0` for the first repository release

### Validation

- `pytest -q`
- `python -m ruff check .`
- `aoa workspace inspect /srv/AbyssOS/aoa-sdk`

### Notes

- this release keeps `aoa-sdk` on the control plane: typed loading, disclosure, compatibility, activation, and handoff helpers rather than runtime ownership
