# Recurrence Control Plane Part Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0012
- Original date: 2026-05-31
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, artifact localization, recurrence control plane, manifest gate, downstream projections, recursor readiness
- Mechanic parents: recurrence
- Guard families: mechanics topology, manifest compatibility, part validation, schema validation, script smoke
- Posture: accepted

## Context

The recurrence parent mechanic still carried active SDK payload in root
technical districts: `docs/RECURRENCE_*.md`, `schemas/*recurrence*`,
`schemas/change_signal.schema.json`,
`examples/recurrence/`, `manifests/recurrence/`, root recurrence scripts, and
root recurrence seed tests.

Those files are not repo-wide root contracts. They implement SDK-local
recurrence carry: manifest scanning, hook observations, graph snapshots, live
observations, beacon pressure, owner review packets, decision closure,
downstream projection guards, wiring handoffs, and recursor readiness scans.

Agents-of-Abyss keeps recurrence as a shared parent mechanic and names the SDK
role as review-only control-plane carry. Sibling repositories keep local owner
truth, proof, routing, stats, KAG, role, and runtime authority.

## Decision

Localize recurrence root payload into active `mechanics/recurrence/parts/`
homes:

- `component-manifest-gate`
- `hook-observation-pack`
- `graph-closure-snapshot`
- `live-observation-producers`
- `beacon-candidate-pressure`
- `owner-review-surface`
- `review-decision-closure`
- `downstream-projection-guard`
- `wiring-rollout-handoff`
- `recursor-readiness`

Keep `src/aoa_sdk/recurrence/` as the importable SDK implementation package. Extend
recurrence manifest and hook loaders to scan part-local manifest districts while
still accepting workspace-owner root `manifests/recurrence/` inputs.

## Rationale

Active paths should expose the operational map: role, input, output, owner,
next route, tools, and validation. Root filenames such as
`RECURRENCE_BEACON_WAVE_INSERT.md` and `tests/test_recurrence_seed.py` describe
landing history or test shape, not the active route.

Splitting recurrence into parts keeps real operational boundaries visible
without creating extra parent mechanics. The SDK can carry typed evidence and
handoff packets, but it does not decide owner meaning or silently install
follow-through.

## Consequences

- Root `docs/`, `schemas/`, `examples/recurrence/`, `manifests/recurrence/`,
  `scripts/`, and `tests/` no longer own active recurrence payload.
- Part-local scripts locate the repository root by searching for
  `src/aoa_sdk`, so they remain executable from active homes.
- Schema `$id` values that existed now point to part-local schema homes.
- Manifest and hook registries scan part-local recurrence manifest districts.
- Old root paths and wave/insert names are provenance only, not active route
  names.

## Source Surfaces

- `src/aoa_sdk/recurrence/`
- `mechanics/recurrence/README.md`
- `mechanics/recurrence/PARTS.md`
- `mechanics/recurrence/PROVENANCE.md`
- `mechanics/recurrence/parts/`
- `mechanics/recurrence/parts/component-manifest-gate/schemas/change_signal.schema.json`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `src/aoa_sdk/recurrence/registry.py`
- `src/aoa_sdk/recurrence/hook_registry.py`
- `src/aoa_sdk/recurrence/wiring.py`

## Follow-Up Route

Continue the root technical district audit for checkpoint, boundary-bridge,
release-support, RPG, antifragility, and any remaining cross-mechanic root
contracts.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
