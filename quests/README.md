# Quest District

This directory holds tracked `aoa-sdk` obligations that should survive the
current diff.

It is not a private scratchpad and not a second roadmap. Program direction
belongs in `ROADMAP.md`. The human open-obligation index is `QUESTBOOK.md`.
Questbook operation law starts in `mechanics/questbook/`.

Quest sources live in lane-first lifecycle directories:

```text
quests/<lane>/<state>/<quest-file>
```

## Operating Card

| Field | Route |
| --- | --- |
| role | SDK source quest record district |
| input | helper follow-through, owner handoff, deferred checkpoint route, or reviewed obligation that must survive a diff |
| output | lane/state source record, `QUESTBOOK.md` open-obligation entry, or handoff to an owning mechanic part |
| owner | `quests/AGENTS.md` for editing law; `mechanics/questbook/` for source-store and lifecycle posture |
| next route | `quests/<lane>/<state>/`, `QUESTBOOK.md`, `mechanics/questbook/`, or the owning mechanic part |
| validation | `quests/AGENTS.md` and `mechanics/questbook/parts/*/VALIDATION.md` |

## Lanes

| Lane | Use |
| --- | --- |
| `agon/` | requested-only SDK helper candidate follow-through below Agon owner authority |
| `checkpoint/` | future reviewed closeout or checkpoint follow-through records |

## Lifecycle States

Each lane may contain:

| State | Use |
| --- | --- |
| `captured/` | public-safe obligation exists, but route shaping is not complete |
| `triaged/` | route-bearing obligation with enough shape to split, promote, or close |
| `ready/` | next owner action is clear and bounded |
| `active/` | currently being advanced by an owner lane |
| `blocked/` | waiting on a named dependency or owner decision |
| `reanchor/` | old route no longer matches; choose a new owner, band, or evidence path |
| `done/` | landed with enough public evidence to leave the active index |
| `dropped/` | intentionally closed without landing, with a visible reason |

## File Families

| Family | Meaning | Guardrail |
| --- | --- | --- |
| `agon/<state>/AOA-SDK-Q-AGON-*.md` | SDK Agon helper candidate follow-through notes | must not grant live Agon authority |
| `agon/<state>/AOSDK-Q-AGON-*.md` | older SDK Agon helper candidate follow-through notes | keep stable IDs until a reviewed rename decision exists |
| `checkpoint/<state>/*.md` | future checkpoint or closeout follow-through records | must route back to Checkpoint mechanics for validation |

## Boundaries

- `QUESTBOOK.md` owns human open-obligation visibility.
- `quests/` owns source quest record placement.
- `mechanics/questbook/` owns operation law, validation posture, and future
  read-model posture.
- Mechanic parts own helper contracts, generated companions, scripts, tests,
  and stop-lines.
- Generated quest readers are not minted in this slice; if added later, they
  must derive from source records and land with a builder and validator.
