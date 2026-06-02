# SDK Mechanics

`mechanics/` is the dispatcher for repeatable SDK operation pressure.

Use this atlas when the work is about an operation around the SDK: typed
facade, consumed sibling surface, checkpoint handoff, recurrence gate,
release support, control-plane capsule, generated reader, or part-local helper
contract. Use `sdk/` for checked public SDK source-home posture and
`src/aoa_sdk/` for the importable Python implementation package.

## Route

1. Choose the package from the map below.
2. Read [mechanics roadmap](ROADMAP.md) when future pressure or package
   direction is involved.
3. Read package `AGENTS.md`, `README.md`, `ROADMAP.md`, `PARTS.md`, and
   `PROVENANCE.md`.
4. Follow the active part route when one exists.
5. Use the part `VALIDATION.md` for executable checks.
6. Update `topology.json` when package, part, source-family, or validation
   routing changes.

## Package Map

| Package | Class | Use for |
| --- | --- | --- |
| [`agon`](agon/README.md) | shared | Agon helper candidates, recurrence adapters, state-packet bindings, and generated candidate registries |
| [`antifragility`](antifragility/README.md) | shared | stress dispatch, reviewed stress carry, and via negativa posture |
| [`boundary-bridge`](boundary-bridge/README.md) | shared | typed facades, consumed-surface gates, skill bridges, technique readers, and owner-layer handoff |
| [`checkpoint`](checkpoint/README.md) | shared | checkpoint capture, review gates, closeout handoff, child-task re-entry, and reviewed context carry |
| [`codex-projection`](codex-projection/README.md) | shared | workspace MCP, rollout status readouts, portability boundaries, and rollout reference handoff |
| [`experience`](experience/README.md) | shared | Experience helper contracts for capture, adoption, deployment, governance, and office release trains |
| [`questbook`](questbook/README.md) | shared | SDK obligation source records, public obligation posture, lifecycle vocabulary, and dispatch-reader posture |
| [`recurrence`](recurrence/README.md) | shared | manifests, hooks, graph closure, observations, review, projection, rollout, and recursor readiness |
| [`release-support`](release-support/README.md) | shared | changelog, release audit, CI posture, build, publication helper, and sibling canary support |
| [`rpg`](rpg/README.md) | shared | RPG typed consumer API and surface path transport without gameplay authority |
| [`runtime-seam`](runtime-seam/README.md) | shared | workspace roots, source/runtime mirror boundary, control-plane capsule, bootstrap, and local seam routing |
| [`titan`](titan/README.md) | shared | Titan helper contracts for runtime receipts, console, appserver, memory, session replay, and swarm closeout |

## Root Contract

Root `mechanics/` owns only the atlas, the active machine map, and minimal
future-pressure router and test glue:

- `README.md` for human route selection.
- `AGENTS.md` for local edit law.
- `ROADMAP.md` for mechanics-wide future-pressure routing.
- `topology.json` for package order, source-family routes, active part routes,
  validation route lists, and legacy index registration.
- `conftest.py` for shared part-local pytest fixtures.

Do not add root rosters, prep reports, migration ledgers, backlogs, templates,
or generic holding areas. Active operation detail belongs in the owning
package or part. Package-local future pressure belongs in package
`ROADMAP.md`. Durable rationale belongs in `docs/decisions/`. Former-path
accounting belongs in package `PROVENANCE.md` and package-local `legacy/`
indexes when needed.

## Placement

- SDK implementation stays under `src/aoa_sdk/`.
- Checked public SDK posture stays under `sdk/`.
- Mechanics-owned docs, schemas, examples, config, manifests, builders,
  generated companions, and focused tests live under
  `mechanics/<package>/parts/<part>/`.
- Root generated read models stay root-published only when they are consumed
  outside one mechanic.
- Root command wrappers stay in `scripts/` only as repo-wide validators,
  release gates, shared builders, or public compatibility entrypoints.
- Source quest records stay in root `quests/<lane>/<state>/`; helper contracts
  stay part-local.

## Stop Lines

- A mechanic is not sibling source truth.
- A mechanic is not a proof verdict.
- A mechanic is not durable memory.
- A mechanic is not runtime activation.
- A mechanic is not a generated-reader source.
- A dry-run helper is not a release.
- Legacy accounting is not the active route for current behavior.

## Validation

Use the touched part `VALIDATION.md` for focused checks. For package, part,
source-family, root-district, roadmap, or route-card changes, run the
mechanics topology gate from the root route card. Release-facing changes
continue through the repository release gate.
