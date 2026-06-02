# SDK Mechanics Roadmap Router

This roadmap routes future mechanics pressure for `aoa-sdk`.

Use it when the question is "which mechanic owns the next operation contour?",
not "which shipped part should I open?"

Root `ROADMAP.md` owns repo-level SDK direction. `mechanics/README.md` owns the
package atlas. Package `ROADMAP.md` files own package-local future pressure.

## Authority

`mechanics/ROADMAP.md` owns:

- mechanics-level future-pressure routing;
- the rule for when package roadmaps should move;
- mechanics-wide stop lines that keep operation helpers below source truth.

It does not own release history, package inventories, part-local validation,
source-family routes, durable rationale, generated companions, or sibling
owner truth.

Use the stronger surface when the change is narrower:

- repo-level SDK direction: [root roadmap](../ROADMAP.md);
- mechanics package atlas: [mechanics README](README.md);
- machine-readable topology: [topology](topology.json);
- package entry route: `mechanics/<package>/README.md`;
- package future contour: `mechanics/<package>/ROADMAP.md`;
- package part map: `mechanics/<package>/PARTS.md`;
- package source accounting: `mechanics/<package>/PROVENANCE.md`;
- part-local validation: `mechanics/<package>/parts/<part>/VALIDATION.md`;
- durable rationale: [decision records](../docs/decisions/README.md).

## Update Rule

Update this router only when mechanics-wide direction, package-roadmap routing,
package set posture, mechanics-to-source interface, or future-pressure
classification changes.

For local package future pressure, update only the owning package
`ROADMAP.md`. For checked landings, update the source surface, part route,
`PARTS.md`, `PROVENANCE.md`, `topology.json`, tests, or changelog as needed.

Do not duplicate backlog text across packages.

## Current Contour

The mechanics tree is in active part-localized topology. The current contour is
not package discovery; that is already handled by `mechanics/README.md` and
`mechanics/topology.json`.

The current work is future-pressure separation:

- root `ROADMAP.md` stays repo-level direction;
- `mechanics/ROADMAP.md` routes mechanics-wide pressure;
- package `ROADMAP.md` files hold package-local future contours;
- package `README.md` files stay entry cards;
- `PARTS.md` files stay active part maps;
- `PROVENANCE.md` files stay source accounting;
- part `VALIDATION.md` files stay executable check routes.

## Package Future Routes

| Package | Future pressure owner |
| --- | --- |
| [`agon`](agon/ROADMAP.md) | Agon helper candidates, registries, recurrence adapters, and state-packet review bindings |
| [`antifragility`](antifragility/ROADMAP.md) | stress dispatch, reviewed stress carry, and via negativa pruning |
| [`boundary-bridge`](boundary-bridge/ROADMAP.md) | typed facades, consumed-surface gates, skill bridges, technique readers, and owner-layer handoff |
| [`checkpoint`](checkpoint/ROADMAP.md) | checkpoint capture, review gates, closeout handoff, child-task re-entry, and reviewed carry |
| [`codex-projection`](codex-projection/ROADMAP.md) | workspace MCP, rollout readouts, portability boundaries, and owner rollout references |
| [`experience`](experience/ROADMAP.md) | Experience helper contracts for capture, adoption, deployment, governance, and office release trains |
| [`questbook`](questbook/ROADMAP.md) | SDK obligation source records, public obligation posture, lifecycle vocabulary, and dispatch-reader posture |
| [`recurrence`](recurrence/ROADMAP.md) | recurrence manifests, observation, graph closure, owner review, downstream projection, rollout, and readiness |
| [`release-support`](release-support/ROADMAP.md) | changelog, release audit, CI posture, build, publication helper, and sibling canary support |
| [`rpg`](rpg/ROADMAP.md) | RPG typed consumer API and surface path transport |
| [`runtime-seam`](runtime-seam/ROADMAP.md) | workspace roots, source/runtime mirror boundary, control-plane capsule, bootstrap, and local seam routing |
| [`titan`](titan/ROADMAP.md) | Titan helper contracts for runtime receipts, console, appserver, memory, session replay, and swarm closeout |

## When The Time Comes

- Add a new mechanic parent only when an existing parent would become less
  clear by owning the pressure and the new parent has an independent operation,
  owner split, and validator.
- Add a new part only when repeated operation pressure needs a stable route,
  local contract, and validation lane.
- Promote helper behavior only after the source owner has named meaning,
  rollback posture, approval posture, and stop lines.
- Add generated mechanics companions only after source builders and owner routes
  are stronger than the generated output.
- Widen CLI or orchestration behavior only after compatibility and workspace
  posture remain explicit under sibling drift.

## Stop Lines

- Mechanics route repeatable SDK operations; they do not author sibling
  meaning.
- A helper is not activation.
- A dry run is not a release.
- A generated reader is not source truth.
- A checkpoint or closeout carry packet is not memory, proof, progression, or
  owner acceptance.
- Runtime seam posture is not runtime deployment authority.
- Package roadmaps are not landing logs, release ledgers, validation command
  stores, or part inventories.
