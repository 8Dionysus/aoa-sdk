# aoa-sdk Boundaries

`aoa-sdk` exists to consume source-owned generated surfaces and provide typed
Python access to them. It should stay narrow enough that neighboring
repositories remain authoritative.

## Source Ownership

- `aoa-routing` owns navigation surfaces and the dispatch ABI.
- `aoa-skills` owns skill execution canon and activation meaning.
- `aoa-agents` owns role contracts, phase seams, and handoff doctrine.
- `aoa-playbooks` owns scenario composition surfaces.
- `aoa-memo` owns recall and memory objects.
- `aoa-evals` owns proof surfaces and verdict meaning.
- `Dionysus` owns seed lineage, not runtime authority for the SDK.

## aoa-sdk Should Own

- typed loaders over published surfaces
- local workspace discovery and sibling-repo resolution
- shared Python models for stable consumer use
- session and orchestration helpers that preserve source ownership
- policy-aware guards around approval, mutation, and trust posture
- adapters that can change transport without changing ownership
- reviewed-session closeout helpers that call owner-owned publisher scripts and
  refresh derived stats without taking over workflow or proof meaning

## aoa-sdk Should Not Absorb

- authored markdown as the primary runtime API
- copied catalogs from sibling repositories
- hidden ranking, routing, or memory policy
- daemon or service responsibilities
- project-specific overlays inside portable-core modules

## Practical Rule

Before adding an API, ask three questions:

1. Is it reading or wrapping a source-owned published surface?
2. Does the owning repository remain the place where meaning changes?
3. Can the same API stay valid if transport later changes from local files to
   export bundles or MCP?

If the answer is no, the change likely belongs in a sibling repository instead
of `aoa-sdk`.
