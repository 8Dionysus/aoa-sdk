# Boundary Bridge Parts

| Part | Role | Active payload |
| --- | --- | --- |
| `consumed-surface-posture-gate` | Check whether sibling-owned surfaces are safe to read before SDK facades trust them. | compatibility, CLI, and typed facade tests |
| `skill-runtime-bridge` | Keep skill-router recommendations, host inventory, and runtime session files explicit while `aoa-skills` owns skill meaning. | docs, tests, and `src/aoa_sdk/skills/` route references |
| `technique-promotion-readiness-reader` | Read `aoa-techniques` promotion readiness through the SDK facade without claiming technique authority. | tests and `src/aoa_sdk/techniques/` route references |
| `owner-layer-signal-handoff` | Detect owner-layer signals, preserve them through reviewed handoff, and keep them non-executable until an owner route accepts them. | docs, tests, and `src/aoa_sdk/surfaces/` route references |

Candidate-only boundary bridge parts stay listed in
`mechanics/boundary-bridge/PARTS.md` until they have part-local payload.
