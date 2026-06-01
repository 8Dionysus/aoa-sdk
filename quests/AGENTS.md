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

## Read Before Editing

Read root `AGENTS.md`, `QUESTBOOK.md`, `quests/README.md`, and
`mechanics/questbook/README.md`.

If a quest points at an SDK helper part, read that part's `README.md`,
`CONTRACT.md`, and `VALIDATION.md` before changing the quest.

## Route Rules

- Source quest records live in `quests/<lane>/<state>/<quest-file>`.
- `QUESTBOOK.md` is the human open-obligation index.
- `mechanics/questbook/` owns quest source-store law, lifecycle posture,
  public-index posture, and dispatch-reader posture.
- Roadmap direction stays in `ROADMAP.md`.
- Single-mechanic helper payload stays in `mechanics/<parent>/parts/<part>/`.
- Do not add top-level quest aliases.

## Validation

Run the narrowest relevant checks first. Usual checks for this district:

```bash
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py --strict-advisory --fail-on-untracked
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
```

## Closeout

Report changed quest IDs, whether `QUESTBOOK.md` changed, which mechanics part
owns the helper or handoff referenced by the quest, and which validation ran.
