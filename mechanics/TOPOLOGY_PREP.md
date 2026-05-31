# Mechanics Topology Prep

Status: source inventory for the first `aoa-sdk` mechanics skeleton.

This file records the analysis basis for `mechanics/`. It is intentionally a
topology prep surface, not a payload migration log.

## Inventory Basis

The first pass used tracked files only, so transient caches and local runtime
artifacts do not shape the skeleton.

```text
tracked files: 1000
```

Top-level tracked distribution:

| District | Count | Reading |
| --- | ---: | --- |
| `.agents` | 211 | portable skill exports consumed by SDK skill routing |
| `.aoa` | 2 | workspace metadata and local route card |
| `.github` | 7 | CI and GitHub landing surfaces |
| root singletons | 9 | public entry, design, route law, release, package metadata |
| `config` | 12 | Agon seed inputs |
| `docs` | 152 | authored boundaries, API contracts, recurrence, Agon, Titan, closeout, release |
| `examples` | 112 | public-safe fixtures and schema examples |
| `generated` | 14 | lower-authority control-plane companions |
| `githooks` | 4 | optional active-session git boundary integration |
| `manifests` | 21 | recurrence component and hook manifests |
| `quests` | 12 | Agon helper quest candidates |
| `schemas` | 122 | SDK helper contract schemas |
| `scripts` | 49 | builders, validators, operators, release checks |
| `src` | 106 | importable typed SDK source |
| `systemd` | 3 | optional bounded closeout inbox automation |
| `tests` | 164 | regression, fixture, schema, CLI, and route checks |

Extension distribution:

| Extension | Count | Reading |
| --- | ---: | --- |
| `.json` | 356 | schemas, examples, generated companions, config, manifests, fixtures |
| `.md` | 286 | route cards, docs, decisions, skill exports, examples |
| `.py` | 240 | SDK source, tests, builders, validators, operator scripts |
| `.svg` | 50 | documentation and skill assets |
| `.yaml` | 44 | skill metadata and workflow support |
| no extension | 5 | license and hook/runtime command files |
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
- `githooks/AGENTS.md`
- `schemas/AGENTS.md`
- `src/aoa_sdk/AGENTS.md`
- `systemd/AGENTS.md`

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
| `rpg` | 4 | typed RPG registry, models, and surface-path helpers |
| root package | 4 | SDK public API, models, errors, package init |
| `surfaces` | 3 | additive surface registry and heuristics |
| `stats` | 3 | source coverage, profile, and regrounding signals |
| `routing` | 3 | picker and hints over loaded surfaces |
| `loaders` | 3 | typed JSON/file loading |
| `codex` | 3 | workspace MCP and Codex deploy-status registry |
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

## Contract Family Inventory

Schema families:

| Family | Count | Candidate mechanic |
| --- | ---: | --- |
| recurrence | 34 | `recurrence` |
| titan | 31 | `titan` |
| agon | 24 | `agon` |
| experience API | 22 | `experience` |
| checkpoint and closeout | 6 | `checkpoint`, `closeout` |
| workspace | 1 | `workspace-topology` |

Example families:

| Family | Count | Candidate mechanic |
| --- | ---: | --- |
| recurrence | 47 | `recurrence` |
| experience API | 23 | `experience` |
| titan | 17 | `titan` |
| agon | 11 | `agon` |
| checkpoint and closeout | 7 | `checkpoint`, `closeout` |
| A2A return | 5 | `a2a-return` |

Test families:

| Family | Count | Candidate mechanic |
| --- | ---: | --- |
| Agon | 13 | `agon` |
| recurrence | 12 | `recurrence` |
| control plane | 11 | `workspace-topology`, `compatibility`, `boundary-bridge` |
| Titan | 8 | `titan` |
| A2A | 6 | `a2a-return` |
| checkpoint and closeout | 5 | `checkpoint`, `closeout` |
| Experience | 4 | `experience` |
| release support | 2 | `release-support` |

## Derivation Rules

The skeleton uses a package only when the operation has all of these:

- repeated pressure across more than one repository district;
- a clear trigger;
- a bounded SDK-owned handle or helper;
- a stronger owner split;
- current source surfaces that can be named today;
- a stop-line that prevents SDK source or sibling meaning absorption;
- at least one validation route.

If an operation is only a module name, it stays in `src/aoa_sdk/`.
If an operation is only a document theme, it stays in `docs/`.
If an operation already belongs to a sibling owner, SDK mechanics may route the
handoff but must not claim the meaning.

## First Skeleton Packages

| Mechanic | Trigger | SDK owns | Stronger owner split |
| --- | --- | --- | --- |
| `workspace-topology` | workspace root, mirror, or bootstrap changes | explicit local path resolution and control-plane capsule | host layout, sibling repo content, runtime mirror deployment |
| `compatibility` | consumed sibling surface path or version drift | stable surface IDs and checks over consumed paths | sibling topology and meaning |
| `boundary-bridge` | typed facade or source-owner boundary changes | SDK handle, typed model, truth label, handoff route | sibling source truth and policy |
| `skill-routing` | skill discovery, disclosure, activation, guard, or dispatch changes | skill-only portable helper behavior | `aoa-skills` skill canon and activation meaning |
| `surface-detection` | non-skill owner-layer candidate detection or handoff | additive hints, shortlist, receipts, reviewed handoff route | eval, memo, playbook, agent, technique, and owner-layer meaning |
| `checkpoint` | mid-session note capture, hook, review-note, or bridge context changes | session-local capture and fail-closed review gates | durable memory, proof, progression, and owner verdicts |
| `closeout` | reviewed closeout request, inbox, manifest, or followthrough changes | mechanical request/inbox/manifest assembly and owner handoff | reviewed owner receipts, harvest, memory, proof, and progression meaning |
| `recurrence` | recurrence manifests, hooks, graph, review, projections, observations | SDK recurrence control-plane helpers and validators | owner component truth and eval-suite proof |
| `agon` | Agon helper candidate, registry, quest, or seed update | candidate-only SDK helper packs and generated registries | Agon doctrine, verdict, duel, KAG, Sophian, and state-packet meaning |
| `titan` | Titan harness, console, appserver, memory, session, or swarm helper changes | bounded Titan control-plane API and CLI surfaces | Titan runtime, identity, memory, and role authority |
| `experience` | SDK API helper contract for adoption, deployment, governance, release | typed call contracts, schemas, examples, validation | Experience owner truth and operational decisions |
| `a2a-return` | summon, checkpoint, reviewed closeout, or return transition changes | return packet bridge and local typed assembly | A2A role handoff, memo proof, progression, and stress verdict meaning |
| `rpg` | RPG typed consumer or surface-path change | typed registry and path helper | RPG runtime/gameplay semantics |
| `codex-plane` | Codex workspace MCP, deploy status, rollout ref, or portability change | typed local read and MCP exposure | Codex runtime, host deployment, and sibling rollout authority |
| `release-support` | changelog, release audit, CI, build, or publish helper changes | bounded release audit and support posture | GitHub release truth, package publication, and sibling releases |

## Payload Movement Rule

This first skeleton does not move source files, schemas, examples, generated
files, manifests, quests, scripts, or tests into mechanics packages.

A later payload move needs a separate decision or update, a package-local
validator, a compatibility note, and source-owner closeout. Until then,
mechanic `PARTS.md` files are candidate topology only.

## Validation

The narrow gate for this skeleton is:

```bash
python scripts/validate_mechanics_topology.py
```

The release gate includes this validator so package cards, source-surface
references, and root route law cannot silently drift.
