# Mechanics Topology Prep

Status: source inventory for the first `aoa-sdk` mechanics topology draft.

This file records the analysis basis for `mechanics/`. It is intentionally a
topology prep surface, not a payload migration log.

## Inventory Basis

The first pass used tracked files only, so transient caches and local runtime
artifacts do not shape the topology draft.

```text
tracked files: 1056
```

Top-level tracked distribution:

| District | Count | Reading |
| --- | ---: | --- |
| `.agents` | 211 | portable skill exports consumed by SDK skill routing |
| `.aoa` | 2 | workspace metadata and local route card |
| `.github` | 7 | CI and GitHub landing surfaces |
| root singletons | 9 | public entry, design, route law, release, package metadata |
| `config` | 12 | Agon seed inputs |
| `docs` | 154 | authored boundaries, API contracts, decisions, recurrence, Agon, Titan, closeout, release |
| `examples` | 112 | public-safe fixtures and schema examples |
| `generated` | 14 | lower-authority control-plane companions |
| `manifests` | 21 | recurrence component and hook manifests |
| `mechanics` | 52 | operation topology cards, parts, provenance, and validator inputs |
| `quests` | 12 | Agon helper quest source records |
| `schemas` | 122 | SDK helper contract schemas |
| `scripts` | 50 | builders, validators, operators, release checks |
| `src` | 106 | importable typed SDK source |
| `tests` | 165 | regression, fixture, schema, CLI, and route checks |

Extension distribution:

| Extension | Count | Reading |
| --- | ---: | --- |
| `.json` | 357 | schemas, examples, generated companions, config, manifests, fixtures |
| `.md` | 339 | route cards, docs, decisions, mechanics, skill exports, examples |
| `.py` | 242 | SDK source, tests, builders, validators, operator scripts |
| `.svg` | 50 | documentation and skill assets |
| `.yaml` | 44 | skill metadata and workflow support |
| no extension | 5 | license and part-local Git hook templates |
| `.yml` | 5 | GitHub workflow support |
| `.example` | 5 | hook template examples |
| `.toml` | 3 | package and workspace metadata |
| `.jsonl` | 2 | Titan event streams |
| `.service` | 1 | closeout user service unit |
| `.path` | 1 | closeout user path unit |
| `.gitkeep` | 1 | empty directory marker |
| `.gitignore` | 1 | repository ignore policy |

Local route cards before this landing:

- `AGENTS.md`
- `.aoa/AGENTS.md`
- `.github/AGENTS.md`
- `docs/decisions/AGENTS.md`
- `generated/AGENTS.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/AGENTS.md`
- `schemas/AGENTS.md`
- `src/aoa_sdk/AGENTS.md`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/AGENTS.md`

`mechanics/AGENTS.md` becomes the local route card for this new topology
district.

## Source Family Inventory

`src/aoa_sdk/` already shows the operation pressure that mechanics should map:

| Source family | Files | Topology reading |
| --- | ---: | --- |
| `recurrence` | 26 | manifest, graph, review, projection, observation, readiness, and CLI operation |
| `a2a` | 15 | summon, checkpoint, closeout, memo, progression, stress, passport, and return bridge |
| `titans` | 6 | runtime, console, appserver, memory, session, and swarm control-plane helpers |
| `skills` | 6 | discovery, disclosure, activation, detector, and runtime session support |
| `workspace` | 5 | root discovery, config, roots, and portable bootstrap |
| `rpg` | 4 | typed RPG consumer API, models, and surface-path transport helpers |
| root package | 5 | SDK public API, models, errors, package init, source route card |
| `surfaces` | 3 | additive surface registry and heuristics |
| `stats` | 3 | source coverage, profile, and regrounding signals |
| `routing` | 3 | picker and hints over loaded surfaces |
| `loaders` | 3 | typed JSON/file loading |
| `codex` | 3 | workspace MCP server source and Codex live rollout status registry |
| `techniques` | 2 | sibling facade |
| `release` | 2 | release audit and publish helper API |
| `playbooks` | 2 | sibling facade |
| `memo` | 2 | sibling facade |
| `kag` | 2 | sibling facade |
| `governed_runs` | 2 | sibling facade |
| `evals` | 2 | sibling facade |
| `compatibility` | 2 | consumed sibling-surface policy |
| `closeout` | 2 | reviewed closeout helper API |
| `cli` | 2 | command surface |
| `checkpoints` | 2 | checkpoint registry |
| `agents` | 2 | phase binding facade |

## Source Family Route Crosswalk

Every tracked `src/aoa_sdk/*` source family has one primary mechanic route.
This prevents a module family from being mistaken for a parent mechanic solely
because it has files.

| Source family | Primary mechanic | Reading |
| --- | --- | --- |
| root package | `boundary-bridge` | public API, model labels, errors, and source route law are facade/truth-label surfaces |
| `a2a` | `checkpoint` | summon return and re-entry helpers are checkpoint/closeout return parts |
| `agents` | `boundary-bridge` | phase bindings read sibling-owned surfaces |
| `checkpoints` | `checkpoint` | checkpoint registry and review gates are the parent operation |
| `cli` | `boundary-bridge` | cross-mechanic command facade; follow the command's owning mechanic after entry |
| `closeout` | `checkpoint` | reviewed closeout is a checkpoint bridge part |
| `codex` | `codex-projection` | workspace MCP server and live rollout status readers project Codex-facing state |
| `compatibility` | `boundary-bridge` | compatibility policy bridges consumed sibling surfaces |
| `evals` | `boundary-bridge` | eval readers are typed handles over proof-owner surfaces |
| `governed_runs` | `boundary-bridge` | governed-run artifacts bridge abyss-stack and playbook review targets |
| `kag` | `boundary-bridge` | KAG readers expose owner surfaces without canonization authority |
| `loaders` | `boundary-bridge` | JSON loaders are surface-access substrate for facades |
| `memo` | `boundary-bridge` | memo readers expose memory-owner surfaces |
| `playbooks` | `boundary-bridge` | playbook readers expose activation, handoff, and governance surfaces |
| `recurrence` | `recurrence` | manifests, graph, hooks, projections, review, and observation form the parent operation |
| `release` | `release-support` | audit and publish helpers support release gates |
| `routing` | `boundary-bridge` | routing hints bridge tasks to owner surfaces |
| `rpg` | `rpg` | RPG typed consumer helpers form the RPG parent operation |
| `skills` | `boundary-bridge` | discovery and dispatch remain below `aoa-skills` ownership |
| `stats` | `boundary-bridge` | stats readers expose `aoa-stats` surfaces without owning stats truth |
| `surfaces` | `boundary-bridge` | detection reports are advisory bridge and handoff surfaces |
| `techniques` | `boundary-bridge` | technique promotion readiness readers expose `aoa-techniques` surfaces |
| `titans` | `titan` | Titan helper families form the Titan parent operation |
| `workspace` | `runtime-seam` | root discovery, config, and bootstrap are runtime/source seam surfaces |

Checkpoint reviewed closeout context carry is now a functioning part-local
payload under `mechanics/checkpoint/parts/reviewed-closeout-context-carry/`.
The path names the active operation: reviewed closeout context in, advisory
carry packets out, owner truth routed away.

Boundary Bridge skill runtime bridge is now a functioning part-local payload
under `mechanics/boundary-bridge/parts/skill-runtime-bridge/`. The path names
the active operation: skill-router and host inventory signals in, explicit
actionability reporting out, skill meaning routed back to `aoa-skills`.

Release Support detailed runbook and public support CI posture are now
functioning part-local payloads under `mechanics/release-support/parts/`.
Root release docs remain active route doors because federation release
preflight and public onboarding need stable entry surfaces.

## Contract Family Inventory

Schema families:

| Family | Count | Candidate mechanic |
| --- | ---: | --- |
| recurrence | 34 | `recurrence` |
| titan | 31 | `titan` |
| agon | 24 | `agon` |
| experience API | 22 | `experience` |
| checkpoint and closeout | 6 | `checkpoint` |
| workspace | 1 | `runtime-seam` |

Example families:

| Family | Count | Candidate mechanic |
| --- | ---: | --- |
| recurrence | 47 | `recurrence` |
| experience API | 23 | `experience` |
| titan | 17 | `titan` |
| agon | 11 | `agon` |
| checkpoint and closeout | 7 | `checkpoint` |
| A2A return | 5 | `checkpoint` |

Test families:

| Family | Count | Candidate mechanic |
| --- | ---: | --- |
| Agon | 13 | `agon` |
| recurrence | 12 | `recurrence` |
| control plane | 11 | `runtime-seam`, `boundary-bridge` |
| Titan | 8 | `titan` |
| A2A | 6 | `checkpoint` |
| checkpoint and closeout | 5 | `checkpoint` |
| Experience | 4 | `experience` |
| release support | 2 | `release-support` |

## Derivation Rules

The topology draft uses a package only when the operation has all of these:

- repeated pressure across more than one repository district;
- a clear trigger;
- a bounded SDK-owned handle or helper;
- a stronger owner split;
- current source surfaces that can be named today;
- a stop-line that prevents SDK source or sibling meaning absorption;
- at least one validation route.
- an AoA parent vocabulary match when sibling sources already provide the
  operation parent.

If an operation is only a module name, it stays in `src/aoa_sdk/`.
If an operation is only a document theme, it stays in `docs/`.
If an operation is a narrow SDK lane inside a shared AoA mechanic, it becomes a
part in that mechanic rather than a top-level package.
If an operation already belongs to a sibling owner, SDK mechanics may route the
handoff but must not claim the meaning.

## Corrected Parent Packages

| Mechanic | Trigger | SDK owns | Stronger owner split |
| --- | --- | --- | --- |
| `agon` | Agon helper candidate, registry, or seed update | candidate-only SDK helper packs and generated registries | Agon doctrine, verdict, duel, KAG, Sophian, and state-packet meaning |
| `antifragility` | stress-posture dispatch, reviewed stress closeout carry, or via negativa pruning changes | public-safe examples and control-plane stress routes | owner remediation, proof, deletion, runtime response |
| `boundary-bridge` | typed facade, compatibility, skill bridge, or surface handoff changes | SDK handle, typed model, truth label, checks, handoff route | sibling source truth and policy |
| `checkpoint` | mid-session note capture, hook, review-note, closeout bridge, or return re-entry changes | session-local capture, fail-closed gates, bridge context, return packets | durable memory, proof, progression, and owner verdicts |
| `codex-projection` | Codex MCP, live rollout status, portability boundary, or rollout ref handoff change | typed local Codex-facing read and MCP exposure | Codex runtime, host deployment, and sibling rollout authority |
| `experience` | SDK API helper contract for adoption, deployment, governance, release | typed call contracts, schemas, examples, validation | Experience owner truth and operational decisions |
| `questbook` | source quest records, public obligation index, lifecycle posture, or dispatch-reader posture changes | SDK obligation source placement, human index posture, lifecycle vocabulary, generated-reader posture | helper contracts, proof verdicts, owner acceptance, release truth |
| `recurrence` | recurrence manifests, hooks, graph, review, projections, observations | SDK recurrence control-plane helpers and validators | owner component truth and eval-suite proof |
| `release-support` | changelog, release audit, CI, build, or publish helper changes | bounded release audit and support posture | GitHub release truth, package publication, and sibling releases |
| `rpg` | RPG typed consumer or surface-path transport change | typed consumer API and path helper | RPG runtime/gameplay semantics |
| `runtime-seam` | workspace root, mirror, bootstrap, capsule, or local automation seam changes | explicit local path resolution, control-plane capsule, and local seam routing | host layout, sibling repo content, runtime mirror deployment |
| `titan` | Titan harness, console, appserver, memory, session, or swarm helper changes | bounded Titan control-plane API and CLI surfaces | Titan runtime, identity, memory, and role authority |

`questbook` remains an active parent because sibling repos treat root
`quests/` as a source quest record district and `mechanics/questbook/` as the
operation law for source-store, public-index, lifecycle, and dispatch-reader
posture. Agon helper contracts stay part-local, but durable SDK obligations
live in root `quests/<lane>/<state>/`.

## Legacy Name Routing

The first SDK topology draft promoted several file-family lanes by local pressure.
Those names are not active route ids. Package-local `legacy/INDEX.md` files
preserve the former-name lookup, while active topology uses canonical part
routes:

| Active parent | Active route |
| --- | --- |
| `runtime-seam` | `runtime-seam/workspace-root-resolution` |
| `runtime-seam` | `runtime-seam/portable-workspace-bootstrap` |
| `runtime-seam` | `runtime-seam/control-plane-capsule` |
| `runtime-seam` | `runtime-seam/runtime-mirror-boundary` |
| `boundary-bridge` | `boundary-bridge/consumed-surface-posture-gate` |
| `boundary-bridge` | `boundary-bridge/skill-runtime-bridge` |
| `boundary-bridge` | `boundary-bridge/owner-layer-signal-handoff` |
| `checkpoint` | `checkpoint/session-growth-checkpoint-cycle` |
| `checkpoint` | `checkpoint/reviewed-session-handoff-runner` |
| `checkpoint` | `checkpoint/child-task-reentry` |
| `checkpoint` | `checkpoint/reviewed-closeout-context-carry` |
| `codex-projection` | `codex-projection/workspace-mcp-server` |
| `codex-projection` | `codex-projection/live-rollout-status-readout` |
| `codex-projection` | `codex-projection/portability-boundary` |
| `codex-projection` | `codex-projection/owner-rollout-reference-handoff` |

## Payload Movement Rule

The first topology draft did not move source files, schemas, examples, generated
files, manifests, quests, scripts, or tests into mechanics packages.

The current artifact-localization phase moves single-mechanic-owned payload
only after the owning part has `README.md`, `CONTRACT.md`, `VALIDATION.md`, and
a narrow validator route. Old root paths become migration/provenance evidence,
not active routes.

The placement law and migration ledger now live in
[`ARTIFACT_TOPOLOGY.md`](ARTIFACT_TOPOLOGY.md).

## Validation

The narrow gate for this topology draft is:

```bash
python scripts/validate_mechanics_topology.py
```

The release gate includes this validator so package cards, source-surface
references, and root route law cannot silently drift.
