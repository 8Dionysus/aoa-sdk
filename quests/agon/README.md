# Agon Quest Lane

This lane holds SDK-owned Agon helper follow-through records.

These records keep requested-only helper obligations visible. They do not grant
live Agon protocol authority, verdict authority, rank or retention mutation,
KAG promotion, Tree of Sophia canon writes, hidden scheduler action, or runtime
service activation.

## Current State

`ready/` contains helper candidate follow-through records whose owner route is
clear: the active helper contract lives under `mechanics/agon/parts/*`, while
the durable obligation source record lives here.

## Owner Routes

| Need | Route |
| --- | --- |
| source quest record | `quests/agon/<state>/` |
| human index | `QUESTBOOK.md` |
| quest source-store law | `mechanics/questbook/` |
| helper contract | `mechanics/agon/parts/<part>/` |
| stronger Agon authority | `Agents-of-Abyss` and owner repos named by the helper contract |
