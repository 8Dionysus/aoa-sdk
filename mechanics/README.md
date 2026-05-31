# aoa-sdk Mechanics

Status: skeleton.

`mechanics/` names repeatable SDK operations that already span several
repository districts. It does not move payload out of `src/aoa_sdk/`, `docs/`,
`schemas/`, `examples/`, `generated/`, `scripts/`, or `tests/`.

The skeleton exists so future work can ask a narrower question: which
operation is changing, what does the SDK own, what stronger owner remains
outside, and which validator proves the crossing?

## Source Basis

This topology was derived from the tracked `aoa-sdk` file inventory and then
corrected against live mechanics sources in `Agents-of-Abyss`, `aoa-agents`,
`aoa-memo`, `aoa-evals`, `aoa-skills`, and `aoa-techniques`:

- 1056 tracked files.
- 25 top-level districts or singleton root surfaces.
- 357 JSON files, 339 Markdown files, and 242 Python files.
- active source clusters under `src/aoa_sdk/` for recurrence, A2A, Titan,
  skills, workspace, RPG, surfaces, stats, routing, Codex, release,
  compatibility, checkpoint, closeout, loaders, command facades, and sibling
  facades.
- matching schema, example, generated, script, manifest, quest, and test
  families for recurrence, Agon, Titan, Experience APIs, checkpoint/closeout,
  A2A return, workspace, and release support.
- sibling mechanics repeatedly put narrow lanes under parent `PARTS.md` rather
  than promoting every file family to a parent package.
- `topology.json` carries a `source_family_routes` crosswalk for every
  `src/aoa_sdk/*` family, including root-package files, so new source families
  cannot silently evade a mechanic route.

The detailed inventory and derivation rules live in
[`TOPOLOGY_PREP.md`](TOPOLOGY_PREP.md). The machine-readable package map lives
in [`topology.json`](topology.json).

## Package Registry

| Mechanic | Name type | Operation |
| --- | --- | --- |
| [`agon`](agon/README.md) | shared | Agon SDK helper candidates, registries, recurrence adapters, and candidate-only helper packs |
| [`antifragility`](antifragility/README.md) | shared | stress-context, degraded-mode, via negativa, and closeout stress carry |
| [`boundary-bridge`](boundary-bridge/README.md) | shared | typed facades, compatibility policy, skill bridge, surface handoff, and owner split |
| [`checkpoint`](checkpoint/README.md) | shared | session checkpoint capture, review gates, closeout bridge, and return re-entry |
| [`codex-projection`](codex-projection/README.md) | shared | Codex workspace MCP, deploy-status reads, portability, and rollout refs |
| [`experience`](experience/README.md) | shared | Experience API helper contracts and adoption/deployment/governance calls |
| [`questbook`](questbook/README.md) | shared | quest source records and durable owner-followthrough obligations |
| [`recurrence`](recurrence/README.md) | shared | recurrence manifests, hooks, graph, review, projections, and live observations |
| [`release-support`](release-support/README.md) | shared | changelog, release audit, CI posture, build, and publication gates |
| [`rpg`](rpg/README.md) | shared | RPG typed consumer slice and surface path helper boundary |
| [`runtime-seam`](runtime-seam/README.md) | shared | workspace root, source/runtime mirror boundary, capsule, bootstrap, and local automation seams |
| [`titan`](titan/README.md) | shared | Titan runtime harness, console, appserver, memory, session, and swarm helpers |

## Skeleton Contract

Every package in this skeleton has:

- `AGENTS.md` for local route law.
- `README.md` for the operation card.
- `PARTS.md` for candidate sub-operations.
- `PROVENANCE.md` for current source surfaces and stronger-owner notes.

The package cards use a common shape:

- Operation
- Trigger
- SDK owns
- Stronger owner split
- Current source surfaces
- Candidate parts
- Must not claim
- Validation
- Next route

## Parent Versus Part Rule

Top-level package names follow the shared AoA mechanics vocabulary unless a
repo-local mechanic has a genuinely independent operation, owner split,
stop-line, and validator.

The first skeleton over-promoted several SDK-local lanes. The corrected route
is:

| Former parent candidate | Correct route |
| --- | --- |
| `workspace-topology` | `runtime-seam` part |
| `compatibility` | `boundary-bridge` part |
| `skill-routing` | `boundary-bridge` part |
| `surface-detection` | `boundary-bridge` part |
| `closeout` | `checkpoint` part |
| `a2a-return` | `checkpoint` part |
| `codex-plane` | `codex-projection` part |

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

The validator checks the package registry, package files, required card
sections, root topology map, source-surface references, and nested route-card
registration.
