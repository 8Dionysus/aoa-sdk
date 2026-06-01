# Questbook Parent Withdrawal After Quest Localization

## Status

Superseded by `AOA-SDK-D-0042`.

## Index Metadata

- Decision ID: AOA-SDK-D-0033
- Original date: 2026-06-01
- Surface classes: topology, mechanics, parent boundary
- SDK facets: mechanics topology, parent set, quest routing, active naming
- Mechanic parents: agon
- Guard families: parent boundary, root-surface hygiene, active naming
- Posture: superseded

## Supersession

`AOA-SDK-D-0042` restores root `quests/` as the source quest record district
and restores `mechanics/questbook/` as an active parent package. This decision
is retained as the record of the incorrect withdrawal rationale.

## Context

`questbook` entered the corrected parent set because `aoa-sdk` had a root
`quests/` source store. This superseded decision incorrectly treated those
source records as ordinary Agon helper payload after artifact localization.

It then removed root `quests/` and concluded that keeping an active
`mechanics/questbook/` parent would preserve a parent mechanic without active
source surfaces or active part routes.

## Decision

This superseded decision removed `questbook` from the active `aoa-sdk` parent
set. `AOA-SDK-D-0042` reverses that topology and restores Questbook as active.

Agon helper quest records remain part-local Agon payload. Future repo-wide
quest source-store payload needs a fresh decision, active source surface, part
contract, and validator before restoring a Questbook parent.

## Rationale

Top-level mechanics must represent real repeatable SDK operations with current
source surfaces. A historical root directory or sibling vocabulary match is
not enough.

This keeps parent topology honest: active parent names show current operation
ownership; historical reasoning stays in decisions and topology-prep notes.

## Consequences

- This superseded decision removed `mechanics/questbook/` from active topology.
- It reduced the explicit package set to 11 active parents.
- It removed root `quests/`.
- `AOA-SDK-D-0042` reverses these consequences and restores root `quests/`
  plus active `mechanics/questbook/`.

## Source Surfaces

- `mechanics/topology.json`
- `mechanics/README.md`
- `mechanics/TOPOLOGY_PREP.md`
- `scripts/validate_mechanics_topology.py`
- `scripts/validate_nested_agents.py`
- `tests/test_mechanics_topology.py`
- `tests/test_design_surfaces.py`

## Follow-Up Route

If owner-followthrough quest receipts become stable SDK artifacts, create a
new part-local route first and decide whether it belongs under an existing
parent or restores `questbook` with current evidence.

## Verification

```bash
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
```
