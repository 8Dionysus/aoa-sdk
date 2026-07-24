# Federation Entry ABI

`aoa-routing` can now publish a separate federation entry orientation layer without widening the thin router core.

The governing rule stays unchanged:

**Source repos own meaning. Routing owns navigation.**

For federation entry routing, that rule becomes:

**`aoa-routing` may publish entry cards, but it must not become the authority surface those cards describe.**

## Purpose

This surface exists to give very small models and low-context agents a bounded way to enter the wider AoA / ToS federation.

It is an orientation plane, not an authority plane.

The orientation plane should answer:

- what kind of surface this is
- which repo owns it
- which compact capsule to inspect first
- which source-owned authority surface to trust next
- which bounded next hop is reasonable after that

The authority plane should stay upstream:

- `Agents-of-Abyss` owns AoA root authority
- `Tree-of-Sophia` owns ToS root authority
- `aoa-agents` owns agent and tier authority
- `aoa-playbooks` owns playbook authority
- `aoa-kag` owns KAG doctrine for the derived readiness view

## Model Criterion

The ABI is designed around a `2B-first, GPT-5.4-complete` criterion.

That means:

- a small model should be able to enter the federation through a stable starter without loading whole repositories raw
- a stronger model should still see an explicit, reviewable route rather than a hidden router heuristic

## Published v1 Surface

`aoa-routing` now publishes:

- `generated/federation_entrypoints.min.json`

That surface is schema-backed and additive.
It sits beside the thin router outputs instead of replacing them.

The thin router core remains the same:

- `aoa_router.min.json`
- `cross_repo_registry.min.json`
- `task_to_surface_hints.json`
- `task_to_tier_hints.json`
- `recommended_paths.min.json`
- `pairing_hints.min.json`

## Root Entries

v1 publishes exactly two federation root entries:

- `aoa-root`
- `tos-root`

These are derived entry cards.
They are not new root authorities.

Each root card must include:

- `capsule_surface`
- `authority_surface`
- `next_actions`
- `fallback`
- `risk`
- `next_hops`

## Active And Declared Kinds

v1 active entry kinds:

- `agent`
- `tier`
- `playbook`
- `kag_view`

v1 declared but inactive kinds:

- `seed`
- `tos_node`
- `runtime_surface`

Declared kinds are documented as the next wave only.
They must not appear as active entry cards or tiny-model federation starters in this landing.

## Entry Card Contract

Each `federation_entrypoint` card carries:

- `kind`
- `id`
- `owner_repo`
- `title`
- `capsule_surface`
- `authority_surface`
- `next_actions`
- `fallback`
- `risk`
- `next_hops`

Conventions:

- `capsule_surface` and `authority_surface` use repo-qualified refs: `repo:path`
- `next_actions` use bounded action objects with `verb`, `target_repo`, `target_surface`, `match_key`, and optional `target_value`
- `next_hops` stay bounded and typed

## Anti-Confusion Rules

These are hard constraints for the landing:

- orientation must never point authority at `aoa-routing/generated/*`
- `aoa-routing` may summarize a source surface, but it may not replace it
- root entry cards must keep AoA and ToS authority in their owning repos
- return-oriented re-entry may use router-owned entry cards only as orientation; the first authority surface must still live in the owning repo
- `tos-root` may hand off to one current source-owned ToS tiny-entry route without activating `tos_node`
- KAG views remain derived readiness views, not canon authorship
- the thin router taxonomy for `technique`, `skill`, `eval`, and `memo` must not be widened by this ABI layer

## Tiny-Model Seam

`generated/tiny_model_entrypoints.json` now has a separate federation seam:

- `federation_queries`
- `federation_starters`

This seam is additive.
Existing consumers of `queries` and `starters` for the thin router path should keep working unchanged.

v1 federation starters are:

- `federation-root`
- `aoa-root`
- `tos-root`
- `agent-root`
- `tier-root`
- `playbook-root`
- `kag-view-root`

This wave does not add a separate tiny-entry federation starter.
Small-model ToS entry still begins at `tos-root`.

A dedicated `return_navigation_hints` surface may coexist with federation entry cards so that small-model recovery stays explicit without widening the authority boundary.

## Current v1 Inputs

This first landing stays `aoa-routing`-only by edited files, but it reads sibling source surfaces:

- `Agents-of-Abyss/README.md`
- `Tree-of-Sophia/README.md`
- `Tree-of-Sophia/examples/tos_tiny_entry_route.example.json`
- `aoa-agents/generated/agent_registry.min.json`
- `aoa-agents/generated/model_tier_registry.json`
- `aoa-agents/generated/runtime_seam_bindings.json`
- `aoa-playbooks/generated/playbook_registry.min.json`
- `aoa-kag/generated/federation_spine.min.json`

For the current ToS root card, the first handoff is now:

`tos-root -> Tree-of-Sophia/examples/tos_tiny_entry_route.example.json -> ToS-authored route surfaces`

That handoff is source-owned and bounded.
The current ToS input should treat `bounded_hop` as the primary hop field and
may keep `lineage_or_context_hop` as a temporary compatibility alias while
downstream consumers transition. If both fields are present, they must resolve
to the same in-repo surface.
It does not activate `tos_node` as a live federation entry kind.

The current KAG-view layer now publishes two live derived entries:

- `aoa-techniques` as the default KAG starter for the federation seam
- `Tree-of-Sophia` as the ToS-specific derived KAG view reached from `tos-root`

This does not widen the active kind list.
It only lets `tos-root` hand off to a ToS-shaped derived readiness card after the source-owned tiny-entry route.
In the current wave, that ToS-specific `kag_view` may also advertise one bounded
`aoa-kag/generated/tos_zarathustra_route_retrieval_pack.min.json` adjunct.
That adjunct is handles-only, appears only inside the ToS `kag_view`, and does
not replace `Tree-of-Sophia` authority or grant routing ownership over ToS
meaning.

## Non-Goals

This landing does not:

- turn `aoa-routing` into a second charter layer
- promote declared kinds to active routing
- add a new federation starter for the current ToS tiny-entry route
- turn the bounded `AOA-K-0011` adjunct into a new federation kind or thin-router starter
- replace ToS authority with route-owned cards
- replace KAG doctrine with router-owned summaries
- fold federation entry routing into the thin router registry
- change `kag-view-root` away from the current `aoa-techniques` default
