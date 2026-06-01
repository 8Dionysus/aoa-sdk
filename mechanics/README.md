# aoa-sdk Mechanics

Status: active topology with part-local payload.

`mechanics/` names repeatable SDK operations that already span several
repository districts. It now also hosts functioning part-local payload when a
single mechanic part owns the artifact.

The topology exists so future work can ask a narrower question: which operation
is changing, what does the SDK own, what stronger owner remains outside, where
does the active artifact live, and which validator proves the crossing?

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
[`TOPOLOGY_PREP.md`](TOPOLOGY_PREP.md). The active placement law and migration
ledger live in [`ARTIFACT_TOPOLOGY.md`](ARTIFACT_TOPOLOGY.md). The
machine-readable package map lives in [`topology.json`](topology.json).

## Package Registry

| Mechanic | Name type | Operation |
| --- | --- | --- |
| [`agon`](agon/README.md) | shared | Agon SDK helper candidates, registries, recurrence adapters, and candidate-only helper packs |
| [`antifragility`](antifragility/README.md) | shared | stress-posture dispatch, reviewed stress closeout carry, and via negativa pruning |
| [`boundary-bridge`](boundary-bridge/README.md) | shared | typed facades, compatibility policy, skill runtime bridge, surface handoff, and owner split |
| [`checkpoint`](checkpoint/README.md) | shared | session checkpoint capture, review gates, closeout bridge, return re-entry, and reviewed context carry |
| [`codex-projection`](codex-projection/README.md) | shared | workspace MCP server, live rollout status readouts, portability boundaries, and rollout reference handoffs |
| [`experience`](experience/README.md) | shared | Experience API helper contracts and adoption/deployment/governance calls |
| [`questbook`](questbook/README.md) | shared | source quest records, public obligation index posture, lifecycle vocabulary, and future dispatch-reader posture |
| [`recurrence`](recurrence/README.md) | shared | recurrence manifests, hooks, graph, review, projections, and live observations |
| [`release-support`](release-support/README.md) | shared | changelog, release audit/publish helpers, public support CI posture, build, and publication gates |
| [`rpg`](rpg/README.md) | shared | RPG typed consumer slice and surface path helper boundary |
| [`runtime-seam`](runtime-seam/README.md) | shared | workspace root, source/runtime mirror boundary, capsule, bootstrap, and local automation seams |
| [`titan`](titan/README.md) | shared | Titan runtime harness, console, appserver, memory, session, and swarm helpers |

## Package Contract

Every package has:

- `AGENTS.md` for local route law.
- `README.md` for the operation card.
- `PARTS.md` for candidate sub-operations.
- `PROVENANCE.md` for current source surfaces and stronger-owner notes.

Functioning part-local payload also has:

- `parts/AGENTS.md` for part district route law.
- `parts/README.md` for the active/candidate part index.
- `parts/<part>/README.md` for role, input, output, owner, and next route.
- `parts/<part>/CONTRACT.md` for may/must-not boundaries.
- `parts/<part>/VALIDATION.md` for executable proof.

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

Former parent-name candidates are not active route ids. Their lookup record
lives only in package-local `legacy/INDEX.md` files. Active routes use
topological part names such as `runtime-seam/workspace-root-resolution`,
`boundary-bridge/consumed-surface-posture-gate`,
`boundary-bridge/skill-runtime-bridge`,
`boundary-bridge/owner-layer-signal-handoff`,
`checkpoint/reviewed-session-handoff-runner`,
`checkpoint/reviewed-closeout-context-carry`,
`release-support/release-audit-publish-helper`,
`release-support/public-support-ci-posture`, and
`codex-projection/live-rollout-status-readout`.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

The validator checks the package registry, package files, required card
sections, root topology map, part-local contracts when present,
source-surface references, nested route-card registration, and the root
technical-district allowlist. New single-mechanic payload must land under a
topologically named `mechanics/<parent>/parts/<part>/` owner route instead of
quietly re-opening root `docs/`, `scripts/`, `tests/`, `config/`, `examples/`,
`manifests/`, `githooks/`, or `systemd/` lanes. Root `quests/` is open only
as the Questbook source-record district; helper payload still belongs in
part-local mechanics homes.
