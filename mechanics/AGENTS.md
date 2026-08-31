# AGENTS.md

## Applies to

Everything under `mechanics/`.

## Role

`mechanics/` is the SDK operation topology layer. It names repeatable
cross-surface SDK operations and hosts part-local payload when a single
mechanic part owns the artifact.

Mechanics are operation homes and route maps. They are not the importable SDK
source home.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `AGENTS.md`, `DESIGN.md`, `DESIGN.AGENTS.md`, `docs/decisions/README.md`, `mechanics/README.md`, `mechanics/ROADMAP.md`, `mechanics/topology.json`, `README.md`, `ROADMAP.md`, `PARTS.md`, `PROVENANCE.md`, `CONTRACT.md`, `VALIDATION.md`.

## Boundaries

- Stay on the control plane.
- Keep `src/aoa_sdk/` as the importable Python source home.
- Keep generated companions lower authority than their builders and sources.
- Keep sibling-owned meaning in the sibling repository.
- Top-level package names follow the shared AoA mechanics vocabulary. A
  repo-local top-level mechanic needs evidence that it cannot be a part of an
  existing shared parent.
- Every tracked `src/aoa_sdk/*` family routes through
  `mechanics/topology.json#source_family_routes`. Add or update that route
  before claiming a new source family is covered.
- File-family pressure routes through `PARTS.md`; it does not create a parent
  package by itself.
- Future-facing package pressure routes through package `ROADMAP.md`; it does
  not belong in package `README.md`, `PARTS.md`, or `PROVENANCE.md`.
- Move single-mechanic-owned payload into the nearest
  `mechanics/<parent>/parts/<part>/<district>/` home once the part has a local
  contract and validation route.
- Preserve old-path accounting in package `PROVENANCE.md` or package-local
  legacy receipts. Active work starts from the current route.
- Do not treat topology cards as proof that a source surface has moved; prove
  the move with current paths and validators.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report which mechanic package changed, whether any payload moved, which source
surfaces remain stronger, whether future pressure moved, and which validator
proved the topology.
