# Boundary Bridge Parts

| Part | Role | Active payload |
| --- | --- | --- |
| `consumed-surface-posture-gate` | Check whether sibling-owned surfaces are safe to read before SDK facades trust them. | compatibility, CLI, and typed facade tests |
| `skill-environment-inspector` | Inspect exact owner surfaces and distinct install scopes without routing, dispatch, or session state. | docs, tests, and `src/aoa_sdk/skills/` route references |
| `technique-promotion-readiness-reader` | Read `aoa-techniques` promotion readiness through the SDK facade without claiming technique authority. | tests and `src/aoa_sdk/techniques/` route references |
| `owner-layer-signal-handoff` | Detect owner-layer signals, preserve them through reviewed handoff, and keep them non-executable until an owner route accepts them. | docs, tests, and `src/aoa_sdk/surfaces/` route references |
| `organ-access-control-plane` | Project an explicit OS-private organ registry into bounded discovery and candidate-only plans without absorbing owner meaning or runtime authority. | contracts, schemas, generator, examples, tests, and `src/aoa_sdk/organs/` |
| `route-resolution-control-plane` | Resolve and explain one route deterministically from an exact trusted routing snapshot and pinned owner projection without activation. | contract, source lock, implementation, CLI, and focused tests |

Candidate-only boundary bridge parts stay listed in
`mechanics/boundary-bridge/PARTS.md` until they have part-local payload.
