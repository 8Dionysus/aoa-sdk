# Recurrence Route-Role Branches

## Status

Accepted.

The route-role split remains accepted, but AOA-SDK-D-0069 supersedes the
`recurrence/live/skills.py` branch and the SDK-owned skill trigger/usage-gap
producer. The remaining live producer, CLI, and contract branches keep their
placement rationale.

## Index Metadata

- Decision ID: AOA-SDK-D-0058
- Original date: 2026-06-03
- Surface classes: source-topology, recurrence, implementation, validation
- SDK facets: importable implementation, recurrence control-plane, route-role branches
- Mechanic parents: recurrence
- Guard families: source topology, recurrence control-plane, downstream projection guard
- Posture: accepted

## Context

The recurrence package already had strong mechanic boundaries, but three files
were carrying too many route roles:

- `live_observations.py` owned the producer facade and every live producer.
- `cli.py` owned the root recur app, sub-app assembly, root commands, hook
  commands, graph commands, live commands, review commands, and downstream
  projection commands.
- `models.py` owned every recurrence typed contract, from component manifests
  through review decisions and downstream projection bundles.

That shape made future recurrence changes too easy to land in broad files
without entering the route they actually served.

## Options Considered

- Keep recurrence as-is because tests were green.
- Split only live observation producers.
- Split only CLI command families.
- Keep compatibility facades and split live producers, command families, and
  typed contract families by route role.

## Decision

Keep the stable compatibility surfaces:

- `recurrence/live_observations.py` keeps `list_live_producers()` and
  `build_live_observation_packet()`.
- `recurrence/cli.py` keeps exported `recur_app`.
- `recurrence/models.py` keeps compatibility re-exports for existing
  `from aoa_sdk.recurrence.models import ...` imports.

Move implementation and contracts into route branches:

- `recurrence/live/common.py` owns shared live observation helpers.
- `recurrence/live/generated.py` owns generated staleness observations.
- `recurrence/live/techniques.py` owns technique intake/readiness observations.
- `recurrence/live/runtime.py` owns runtime evidence selection observations.
- `recurrence/live/playbooks.py` owns playbook harvest observations.
- `recurrence/live/events.py` owns recurrence event repetition observations.
- `recurrence/cli_core.py` owns root recur commands.
- `recurrence/cli_hooks.py` owns hook list/run commands.
- `recurrence/cli_graph.py` owns graph snapshot/diff/closure commands.
- `recurrence/cli_live.py` owns live producer CLI commands.
- `recurrence/cli_review.py` owns review decision CLI commands.
- `recurrence/cli_project.py` owns downstream projection CLI commands.
- `recurrence/contracts/*` owns typed recurrence contract families:
  base literals, manifests, propagation, observations/hooks, beacons/ledger,
  review decisions, downstream projections, and wiring/rollout.

## Rationale

Recurrence is a control-plane helper. It can observe, plan, project, review,
and surface advisory downstream packets, but it must not become owner truth,
hidden scheduling, stats verdict authority, KAG canon transfer, or routing
authority transfer.

The branch names now match the mechanic route that a future agent should enter
before changing behavior.

## Consequences

- Existing import surfaces remain stable.
- Live observation behavior lands in `recurrence/live/*`.
- Recurrence CLI behavior lands in `recurrence/cli_*`.
- Typed contract changes land in `recurrence/contracts/*`, while
  `recurrence/models.py` remains a compatibility re-export.
- Downstream projection guard posture stays explicit and test-backed.

## Source Surfaces

- `src/aoa_sdk/recurrence/live_observations.py`
- `src/aoa_sdk/recurrence/live/`
- `src/aoa_sdk/recurrence/cli.py`
- `src/aoa_sdk/recurrence/cli_core.py`
- `src/aoa_sdk/recurrence/cli_hooks.py`
- `src/aoa_sdk/recurrence/cli_graph.py`
- `src/aoa_sdk/recurrence/cli_live.py`
- `src/aoa_sdk/recurrence/cli_review.py`
- `src/aoa_sdk/recurrence/cli_project.py`
- `src/aoa_sdk/recurrence/models.py`
- `src/aoa_sdk/recurrence/contracts/`
- `mechanics/recurrence/parts/`
- `generated/source_topology.min.json`
- `tests/test_source_topology_index.py`

## Follow-Up Route

Do not add producer implementations to `live_observations.py`, command
behavior to `cli.py`, or new contract families directly to `models.py`. Route
future changes to the named branch that owns the behavior.

`recurrence/hooks.py` remains below medium pressure and should not be split
without a new route-role reason beyond file size.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
