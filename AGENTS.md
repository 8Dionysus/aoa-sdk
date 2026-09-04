# AGENTS.md

Root route card for `aoa-sdk`. A nearer `AGENTS.md` supplies the local delta
for its subtree.

## Purpose and owner lane

`aoa-sdk` is AoA's typed Python SDK and control-plane helper layer. It consumes
source-owned federation surfaces and exposes local-first APIs for discovery,
loading, validation, compatibility, passive inspection, bounded evidence
materialization, and owner-subordinate handoff. It does not become sibling
source truth by consuming a surface.

This repository owns:

- typed SDK facades, workspace discovery, topology resolution, compatibility,
  versioning, CLI inspection, and the source-home manifest under `sdk/`;
- SDK-local statistics and admitted procedures over SDK-owned Titan helpers;
- the compact generated control-plane capsule and its builder contract;
- mechanics packages, topology, provenance, part artifacts, and validation
  routes under `mechanics/`;
- the accepted `AOA-SDK-D-0071` routing-producer succession and
  `AOA-SDK-D-0076` receipt-bound owner switch, plus the artifact-trust,
  route/plan/receipt, lifecycle, evidence, control-plane facade, runner, and
  transport contract families recorded in `docs/decisions/`.

Those accepted contracts do not grant live execution, publication, skill
activation, operator, memo, proof, playbook, quest, role, checkpoint, service,
or frontend authority. Runtime execution and final admission remain with their
owners. Hidden, undocumented heuristics are not SDK contracts.

## Conditional routes

Start here, then open the nearest nested card. Only when the touched path or
semantic question makes them relevant, read `README.md`, design, roadmap,
decisions, generated surfaces, or sibling sources.

| Need | First owner surface |
|---|---|
| SDK implementation or source-home topology | nearest `sdk/**/AGENTS.md`, then `sdk/source_home.manifest.json` |
| mechanic package or part | nearest `mechanics/**/AGENTS.md` |
| control-plane or compatibility form | `DESIGN.md`, then the named source contract |
| agent-card form or validation posture | `DESIGN.AGENTS.md` |
| rationale or supersession | `docs/decisions/AGENTS.md`, then `docs/decisions/README.md` and the indexed decision |
| repository direction | `ROADMAP.md` |
| generated capsule | authored source and builder, then generated output |
| owner-local measurement | `stats/AGENTS.md` |
| admitted SDK procedure | `skills/AGENTS.md` |

## Authority and topology stop-lines

- Root owns repository identity, owner boundaries, route choice, and claim
  limits. Nested cards own only local risk, stronger sources, stop-lines, and
  validation routing.
- Authored source and manifests define meaning. Generated capsules, adapters,
  exports, checkpoint receipts, and runtime mirrors are derived evidence or
  transport.
- Prefer explicit configuration and manifest-driven behavior over magical
  discovery. Keep source checkouts distinct from deployed runtime mirrors.
- Presence never
  becomes selection, activation, capability execution, or owner authority.
- Skill inspection and additive surface detection are passive. Preserve
  owner-subordination and explicit no-execution/no-activation claims; session
  evidence does not create live state.
- Change authored source or builder inputs before generated companions. Do not
  hand-edit a projection to make parity appear green.

For continuity, use `aoa-memo`; raw session evidence remains in `.aoa`, local
memory candidates use the repository port when present, and durable reviewed
memory lands through its owner.

## Inspection and checkpoint route

Use the on-demand procedures in root `VALIDATION.md` only when skills,
checkpoint evidence, or additive surface detection are in scope. Skills inspection is passive only; it does not detect, rank,
dispatch, activate, or create skill-session state. Preserve session-local
evidence, owner-subordination, `skipped_no_active_session`,
`agent_review=pending`, and `capability_execution_claimed=false`. None of
these observations activates a skill or creates live state.

## Design, decisions, and landing

Use `DESIGN.md` when repository shape, source-home placement, source/generated
authority, compatibility, or mechanics placement changes. Use
`DESIGN.AGENTS.md` when the route mesh, reading order, card form, validation
posture, or closeout contract changes. Neither overrides active SDK source,
validators, accepted decisions, nested cards, or sibling truth.

After a structural, ownership, workflow, route-law, compatibility,
validator-authority, public-contract, or topology change, use the decision lane
to determine whether future agents need a durable rationale.

Root and `.github/AGENTS.md` own landing semantics; the complete procedure is
on demand in `VALIDATION.md`. If required CI status, review, merge authority,
or post-merge state cannot be observed, stop rather than infer it.

## Validation route

Use the nearest `VALIDATION.md` whose route explicitly owns the touched
surface. Root [`VALIDATION.md`](VALIDATION.md) owns repository inspection, the
full owner gate, checkpoint review, rollback, and landing. A part route may own
an exact local check or route to a singular root or cross-part owner. Exact
executable checks do not belong in this card.

The canonical selector remains `scripts/release_check.py`; the owner
claim/evidence manifest defines the claim set, the accepted graph runner is the
default scheduler, and the serial command inventory remains the completeness
oracle and rollback route. A shorter prompt does not weaken those authorities.

## Closeout

Closeout states the typed facade, discovery, compatibility, CLI, checkpoint,
or handoff surface changed; the affected source-home branch; whether anything
moved closer to activation; generated parity; checks run and skipped;
remaining risk; and the next owner route. Keep local validation, CI, review,
merge, publication, runtime use, and owner acceptance distinct.

## Retired root reference

The former preserved root-guidance dump is retired from active docs. If one of
its rules still matters, restate it at the smallest current owner surface
instead of recreating a competing root reference.
