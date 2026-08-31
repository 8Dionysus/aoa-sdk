# AGENTS.md

## Applies to

This card applies to `quests/` and all descendants unless a nearer route card
narrows the path.

## Role

`quests/` is the SDK source quest record district. It holds public obligations,
visible work items, and bounded follow-through records that must survive the
current diff.

Stay on the control plane. Quest records may name SDK helper follow-through,
owner handoff, or deferred route pressure, but they do not grant runtime,
verdict, memory, release, Agon, KAG, or Tree of Sophia authority.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `AGENTS.md`, `QUESTBOOK.md`, `quests/README.md`, `mechanics/questbook/README.md`, `README.md`, `CONTRACT.md`, `VALIDATION.md`.

If a quest points at an SDK helper part, read that part's `README.md`, `CONTRACT.md`, and `VALIDATION.md` before changing the quest.

## Route Rules

- Source quest records live in `quests/<lane>/<state>/<quest-file>`.
- `QUESTBOOK.md` is the human open-obligation index.
- `mechanics/questbook/` owns quest source-store law, lifecycle posture,
  public-index posture, and dispatch-reader posture.
- Roadmap direction stays in `ROADMAP.md`.
- Single-mechanic helper payload stays in `mechanics/<parent>/parts/<part>/`.
- Do not add top-level quest aliases.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report changed quest IDs, whether `QUESTBOOK.md` changed, which mechanics part
owns the helper or handoff referenced by the quest, and which validation ran.
