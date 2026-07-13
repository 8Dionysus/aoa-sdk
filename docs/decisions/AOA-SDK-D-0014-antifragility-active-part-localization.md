# Antifragility Active Part Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0014
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, antifragility, control-plane stress posture, closeout carry
- Mechanic parents: antifragility
- Guard families: mechanics topology, part validation, docs routes, active naming
- Posture: accepted

## Context

After the recurrence, boundary-bridge, checkpoint, Titan, Experience, Agon,
and Codex Projection localization slices, Antifragility still carried
single-mechanic payload in root districts:

- `docs/antifragility-control-plane.md`
- `docs/antifragility-closeout-seam.md`
- `docs/VIA_NEGATIVA_CHECKLIST.md`
- `tests/fixtures/antifragility/`
- `tests/test_antifragility_public_surface.py`

These files are not repo-wide contracts. They implement SDK-local
antifragility carry: stress posture narrows dispatch, reviewed closeout carries
stress evidence, and via negativa asks pruning questions before adding helper
surface.

Agents-of-Abyss keeps Antifragility as the shared parent mechanic. Sibling
repositories keep stronger proof, memory, runtime, deletion, and owner-local
repair authority.

## Decision

Localize Antifragility payload into three functioning part homes:

- `mechanics/antifragility/parts/stress-posture-dispatch-gate/`
- `mechanics/antifragility/parts/reviewed-stress-closeout-carry/`
- `mechanics/antifragility/parts/via-negativa/`

Rename active docs, examples, and tests by route role instead of former root
filename:

- stress dispatch input becomes a stress-posture dispatch request example
- stress dispatch result becomes a stress-posture dispatch decision example
- stress closeout manifest becomes a reviewed stress closeout manifest example
- the public-surface regression becomes part-local validation

## Rationale

Active names should give an agent an operational map: role, input, output,
owner, next route, tools, and validation. Root filenames such as
`antifragility-control-plane.md` and `antifragility-closeout-seam.md` named the
topic and old district, not the active part boundary.

The new paths keep the shared parent while making the SDK-local work explicit:

- `stress-posture-dispatch-gate` receives stress posture and outputs a
  narrowing-only dispatch decision
- `reviewed-stress-closeout-carry` receives reviewed evidence refs and outputs
  a closeout carry manifest
- `via-negativa` keeps the shared pruning route visible before adding helpers

## Consequences

- Root `docs/`, `tests/`, and `tests/fixtures/antifragility/` no longer own
  active Antifragility payload.
- Old root paths live in `mechanics/antifragility/PROVENANCE.md` and
  `mechanics/ARTIFACT_TOPOLOGY.md`, not as active fallbacks.
- The active topology now lists Antifragility parts in
  `mechanics/topology.json#active_part_routes`.
- The SDK still does not own proof verdicts, runtime repair, deletion approval,
  owner-local remediation, durable memory, or stats publication.

## Source Surfaces

- `mechanics/antifragility/README.md`
- `mechanics/antifragility/PARTS.md`
- `mechanics/antifragility/PROVENANCE.md`
- `mechanics/antifragility/parts/`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `README.md`

## Follow-Up Route

Continue the root technical district audit for remaining release-support, RPG,
questbook, and cross-mechanic public contracts. Keep old Antifragility root
names in provenance only.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
