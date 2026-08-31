# Prompt-Light Agent Routes And On-Demand Validation

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0105
- Original date: 2026-08-31
- Surface classes: agent guidance, validation, route-law, docs
- SDK facets: agent surface, validation, release support, control-plane routing
- Mechanic parents: release-support
- Guard families: agent mesh, claim/evidence sufficiency, root-surface hygiene, owner authority
- Posture: accepted

## Context

The root and nested `AGENTS.md` mesh correctly protects SDK ownership,
source authority, control-plane boundaries, and local stop-lines. It also
accumulated executable command batteries, inspection procedures, and complete
GitHub landing instructions. Because these cards are inherited agent context,
that procedure is repeatedly paid even when a task does not need it.

The repository already has stronger and more precise validation owners. Part
`VALIDATION.md` files carry human procedures. `scripts/release_check.py`
selects the repository-wide gate. The owner-authored claim/evidence manifest
defines the full claim set, and the accepted validation graph executes it with
an identity-bound receipt. The retained serial `COMMANDS` battery remains the
exact completeness oracle and rollback route under `AOA-SDK-D-0097`.

The pressure is therefore to separate inherited semantic routing from
on-demand procedure without weakening the owner gate, public navigation, or
landing discipline.

## Options Considered

- Keep executable procedures in every applicable `AGENTS.md` card.
- Replace the public and local `README.md` surfaces with agent-only cards.
- Keep `AGENTS.md` semantic, route human procedures through on-demand
  `VALIDATION.md` surfaces, and preserve the existing machine validation
  authorities.

## Decision

Use root and nested `AGENTS.md` as prompt-light semantic route cards. They own
repository or local identity, owner boundaries, source authority, required
reading order, stop-lines, impact-based validation selection, and closeout
claims. They must not duplicate runnable command batteries, inspection
transcripts, or full branch/PR/CI/merge procedures.

Add a root `VALIDATION.md` as the human entrypoint for repository-wide
inspection, focused checks, the full owner gate, serial rollback, checkpoint
review, and landing procedure. Keep exact part-local commands in the nearest
part `VALIDATION.md`. Agent cards route to those surfaces only when the
touched path, risk, or requested operation makes them applicable.

This human procedure layer does not become machine authority. The canonical
repository-wide executable gate remains `scripts/release_check.py`; the
owner-local claim/evidence manifest remains the full claim and dependency
authority; the accepted graph runner remains the default scheduler; and the
serial command inventory remains the completeness oracle and rollback.

Keep root `README.md` as the compact, command-free public front door established
by `AOA-SDK-D-0045`. Local `README.md` files remain human route, role, and
artifact explanations where they add durable value. They are read on demand,
not unconditionally merely because an agent entered a directory. Removing a
README requires a separate proof that its human-facing role, inbound links,
and unique content have moved to a stronger owner surface.

Generated indexes and compact control-plane projections remain derived. Change
their authored inputs or builders first and regenerate them; do not use this
decision to hand-edit a read model.

This decision partially supersedes only the command-placement language in
`AOA-SDK-D-0045`, `AOA-SDK-D-0049`, and `DESIGN.AGENTS.md`. It preserves their
public README, mechanics topology, route-card mesh, and source-authority laws.
It does not change SDK APIs, routing semantics, runtime activation, validation
claims, release admission, or sibling-owner authority.

## Rationale

Inherited guidance is most valuable when every token changes how the agent
interprets ownership, risk, or authority. Procedures are valuable when the
task reaches their boundary. Separating the two keeps the SDK legible to
low-context agents while retaining one discoverable and reviewable place for
humans to run the exact checks.

Binding the lightweight route to the existing claim/evidence authority avoids
the dangerous shortcut of making shorter guidance mean weaker validation.
Preserving README as a human surface also avoids optimizing agent prompt cost
by deleting public or explanatory value.

## Consequences

- Root and local agent cards become shorter and cheaper to inherit.
- Validation and landing procedure remains directly discoverable but is loaded
  only when relevant.
- Tests and validators must reject executable procedure drift back into
  `AGENTS.md` while continuing to check nearest-card coverage and owner
  boundaries.
- Root and local README retention is judged by human/public value, link
  topology, and unique content rather than by a blanket migration rule.
- Full validation strength, graph sufficiency, rollback, CI, review, and merge
  requirements do not change.

## Source Surfaces

- `AGENTS.md`
- `DESIGN.AGENTS.md`
- `README.md`
- `VALIDATION.md`
- `scripts/release_check.py`
- `scripts/validate_nested_agents.py`
- `mechanics/release-support/parts/validation-evidence-graph/config/validation_graph.json`
- `mechanics/release-support/parts/validation-evidence-graph/scripts/validation_graph.py`
- `mechanics/release-support/parts/validation-evidence-graph/VALIDATION.md`
- `docs/decisions/AOA-SDK-D-0045-root-readme-front-door.md`
- `docs/decisions/AOA-SDK-D-0049-mechanics-roadmap-router-and-package-contours.md`
- `docs/decisions/AOA-SDK-D-0097-use-bounded-claim-evidence-dag-for-full-validation.md`

## Follow-Up Route

Update the active root and nested cards, root validation entrypoint, route
tests, and affected human docs against this decision. Preserve every
owner-local command in the nearest validation surface or existing machine
authority before removing it from inherited guidance.

## Verification

Run the decision-index checks, nested-agent and documentation route validators,
focused validation-graph regressions, mechanics topology checks, and the full
owner gate routed through root `VALIDATION.md`.
