# Manual Equivalence Active Lane Naming

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0038
- Original date: 2026-06-01
- Surface classes: active naming, typed model, skill runtime bridge, surface detection
- SDK facets: skill runtime bridge, owner-layer signal handoff, active naming, compatibility input
- Mechanic parents: boundary-bridge
- Guard families: active naming, compatibility alias, route clarity, part validation
- Posture: accepted

## Context

The skill/surface bridge already used `state=manual-equivalent` to say that a
router-only skill recommendation was not directly executed but the same
discipline was preserved visibly.

The execution lane and typed fields still used `manual-fallback` and
`manual_fallback_*`. That made an active SDK surface sound like a fallback path,
even though the intended route is manual equivalence with explicit truth
labeling.

## Decision

Rename the active execution lane and typed fields to manual-equivalence
vocabulary:

- `lane=manual-equivalence`
- `manual_equivalence_allowed`
- `manual_equivalence_note`

Keep old `manual_fallback_*` keys as validation aliases only, so older payloads
can be read without emitting old names as active output.

## Rationale

The active name should describe the thing the SDK is doing now. This route is
not a hidden fallback and not a legacy path. It is a visible manual equivalence
when the host cannot execute a router-recommended skill directly.

Naming the lane by equivalence keeps the operating map clearer: role, input,
output, owner, next route, and validation stay visible without training agents
to treat weaker routes as substitutes for owner truth.

## Consequences

- `src/aoa_sdk/models.py` emits manual-equivalence fields while accepting old
  payload keys as compatibility input.
- `src/aoa_sdk/surfaces/registry.py` emits `lane=manual-equivalence`.
- CLI output says manual equivalence is allowed instead of manual fallback.
- Boundary Bridge docs and tests prove the new active field names and alias
  posture.

## Source Surfaces

- `src/aoa_sdk/models.py`
- `src/aoa_sdk/skills/detector.py`
- `src/aoa_sdk/surfaces/registry.py`
- `src/aoa_sdk/cli/main.py`
- `mechanics/boundary-bridge/parts/skill-runtime-bridge/`
- `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/`

## Follow-Up Route

Future compatibility aliases should be named and tested as compatibility input,
not left as active route vocabulary. If an old field must remain writable for a
release boundary, record that boundary in the owning part contract.

## Verification

```bash
python -m pytest -q mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge.py
python -m ruff check src/aoa_sdk/models.py src/aoa_sdk/skills/detector.py src/aoa_sdk/surfaces/registry.py src/aoa_sdk/cli/main.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge.py
```
