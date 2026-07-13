# Implementation Source Topology Index

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0051
- Original date: 2026-06-03
- Surface classes: source-topology, generated, validation, agent-route
- SDK facets: importable implementation, generated read model, source topology
- Mechanic parents: checkpoint, runtime-seam
- Guard families: source topology, generated freshness, agent routing
- Posture: accepted

## Context

`src/aoa_sdk/` is the importable implementation body of the SDK. It had a
correct topological name, but the tree was increasingly hard for agents to
enter cheaply: large modules such as checkpoint registry, CLI assembly, shared
models, surface registry, closeout API, and recurrence helpers carried real
split pressure.

The `.aoa` session-memory kernel shows the better pattern: raw evidence stays
strong, while generated indexes and atlas entries give agents a small route
surface before they open heavy material.

## Options Considered

- Continue splitting modules by local judgment without an index layer.
- Put a hand-maintained source map inside `src/aoa_sdk/`.
- Add a generated source-topology read model under `generated/`.

## Decision

Add `generated/source_topology.min.json` as a generated read model over
`src/aoa_sdk/`.

The index records the implementation tree, route keys, node kinds, short
roles, line counts, split-pressure signals, evidence refs, and next-route
guidance. It is built by `scripts/build_source_topology_index.py` and checked
by `scripts/validate_source_topology_index.py`.

## Rationale

The SDK implementation should remain the stronger source. A generated index
helps agents see the tree before reading heavy modules, but it must not become
the source of behavior or doctrine.

This mirrors the `.aoa` layering rule without copying its archive domain:
source files are evidence, generated topology is navigation, and route
decisions stay in decision notes, `AGENTS.md`, mechanics, and tests.

## Consequences

- Agents can inspect `generated/source_topology.min.json` before opening large
  implementation files.
- Split pressure becomes visible as a measured route signal rather than a
  vague impression.
- Release checks now fail if the source topology index is stale.
- Future `src/aoa_sdk` cuts should update the generated index and keep roles
  subordinate to source files and route decisions.

## Source Surfaces

- `src/aoa_sdk/AGENTS.md`
- `generated/source_topology.min.json`
- `scripts/build_source_topology_index.py`
- `scripts/validate_source_topology_index.py`
- `scripts/source_topology_common.py`
- `tests/test_source_topology_index.py`
- `scripts/release_check.py`

## Follow-Up Route

Use the index to choose the next route-role split before adding behavior to a
large module. Prefer branches named by owner function, such as topology,
runtime-session, closeout-context, hook-templates, promotion-handoff, CLI
commands, or model families.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
