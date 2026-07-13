# Refactored Sibling Surface Paths

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0003
- Original date: 2026-05-31
- Surface classes: compatibility, sibling topology, generated route
- SDK facets: compatibility policy, control-plane, sibling read path
- Mechanic parents: boundary-bridge
- Guard families: source topology, compatibility check, canonical path
- Posture: accepted

## Context

The refactored AoA repositories moved several generated reader surfaces from
root-level `generated/` paths into stronger owner homes:

- `aoa-memo` memory readers now live under `generated/memory/`;
- `aoa-memo` memory-object readers now live under `generated/memory-objects/`;
- `aoa-memo` checkpoint-to-memory and runtime-writeback surfaces now live under
  mechanic part-local paths;
- `aoa-evals` runtime-candidate readers now live under the audit mechanic's
  candidate-readers part.

`aoa-sdk` still checked several legacy root-level paths first. The live
federation compatibility check therefore reported missing surfaces even though
the sibling owners had valid refactored surfaces.

## Options Considered

- Regenerate root-level compatibility copies in sibling repositories.
- Change SDK surface IDs to include the new physical path names.
- Make the refactored owner-local paths canonical in SDK compatibility policy
  without accepting legacy root-level paths as alternate routes.

## Decision

`aoa-sdk` compatibility rules use the refactored sibling paths as canonical
physical paths. They do not keep the old root-level generated paths as
fallbacks for these migrated surfaces.

Surface IDs remain stable because consumers depend on SDK-level semantic
handles such as `aoa-memo.memory_catalog.min` and
`aoa-evals.runtime_candidate_intake.min`, not on the physical sibling path.

## Rationale

The sibling repositories own the active topology. The SDK should follow their
stronger owner paths without forcing duplicate root-level exports back into the
sibling repos.

Keeping stable SDK surface IDs preserves API continuity without preserving the
old physical topology as a second supported route.

## Consequences

- Live federation compatibility can resolve current refactored `aoa-memo` and
  `aoa-evals` surfaces.
- SDK consumers keep the same surface IDs and typed facades.
- Workspaces that still expose only the old root-level paths now fail
  compatibility for these surfaces, because that is topology drift rather than
  an SDK-supported route.
- Future compatibility repairs should move the canonical path to the stronger
  owner-local path instead of adding fallback copies.

## Source Surfaces

- `src/aoa_sdk/compatibility/policy.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py`
- `docs/decisions/README.md`
- `docs/boundaries.md`
- `DESIGN.md`

## Follow-Up Route

When `aoa-sdk` introduces local `mechanics/`, route this compatibility posture
through the boundary-bridge mechanic or its SDK-local equivalent. Do not turn
compatibility path drift into sibling source ownership or hidden SDK fallback.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
