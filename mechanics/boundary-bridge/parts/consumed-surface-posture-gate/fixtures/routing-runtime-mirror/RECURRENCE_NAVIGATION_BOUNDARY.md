# Recurrence Navigation Boundary

This note defines what `aoa-routing` may safely contribute when recurrence reaches the routing layer.

The governing split stays unchanged:

**Recurrence is the law. Return is the concrete re-entry seam.**

`aoa-routing` may compress the next valid surface for re-entry.
It must not decide whether return is justified, what a checkpoint means, or who owns the next authority judgment.

## Core Rule

Source repos own meaning.
Routing owns navigation.

For recurrence that becomes:

`aoa-routing` may publish bounded re-entry hints back to source-owned surfaces, but it must not become the authority surface those hints describe.

## What Routing May Safely Do

### 1. Point back to the smallest source-owned inspect surface

When a route loses its artifact contract or source boundary, routing may name the smallest public source-owned surface to inspect first.

### 2. Point back to memo-side return support

When checkpoint continuity is needed, routing may point to public memo recall contracts and object-facing inspect surfaces.

Routing does not reinterpret checkpoint semantics.

### 3. Point federation orientation back to source authority

When a small model or bounded actor loses federation orientation, routing may point back to:

- the owning repo authority surface
- the owning repo capsule surface for a live federation kind
- one router-owned fallback card for orientation only

### 4. Stay deterministic and bounded

Return navigation should stay:

- typed
- reviewable
- source-referring
- small-model legible
- free of graph expansion

## What Routing Must Not Do

`aoa-routing` must not:

- classify return events as memory truth
- define retry budgets
- decide role or tier rights
- replace source authority with router-owned summaries
- reinterpret checkpoint packs as if routing authored them
- widen return into graph traversal or open exploration

## Public Landing

The first routing landing is a dedicated derived surface:

- `generated/return_navigation_hints.min.json`

Its job is narrow:

- give runtime and agent layers a compact re-entry map
- point back to source-owned inspect, expand, or recall surfaces
- keep recurrence support separate from source meaning

It does not patch `task_to_surface_hints.json`, `federation_entrypoints.min.json`, or `tiny_model_entrypoints.json`.

## Consumer Boundary

- `abyss-stack` may consume return-navigation hints to rebuild a bounded context pack, but runtime policy stays outside routing.
- `aoa-agents` may consume return hints to choose the next valid surface after a governed return decision, but return semantics stay outside routing.
- `aoa-playbooks` may cite return hints as scenario-level re-entry help, but choreography stays outside routing.
- `aoa-memo` remains the source for checkpoint continuity and recall contracts; routing only points to those public memo surfaces.

## Anti-Patterns

Treat these as boundary failures:

- a return hint whose primary authority target is `aoa-routing/generated/*`
- a router-owned explanation that replaces the source repo note
- a thin-router return that falls back to a router-owned surface
- a return surface that widens into graph traversal
- a return hint that hides the owning repo
