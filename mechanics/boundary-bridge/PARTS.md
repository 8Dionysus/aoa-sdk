# Boundary Bridge Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| consumed-surface-posture-gate | `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`, `src/aoa_sdk/compatibility/policy.py`, `src/aoa_sdk/artifacts/`, typed facade readers | active; checks whether consumed sibling surfaces are safe to read before SDK code trusts them |
| skill-environment-inspector | `mechanics/boundary-bridge/parts/skill-environment-inspector/`, `src/aoa_sdk/skills/` | active; preserves owner and scope boundaries while inspecting exact bundle, profile, graph, and installation state |
| technique-promotion-readiness-reader | `mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/`, `src/aoa_sdk/techniques/` | active; reads `aoa-techniques` promotion readiness without claiming technique authority |
| owner-layer-signal-handoff | `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/`, `src/aoa_sdk/surfaces/` | turns advisory surface signals into reviewed owner-layer handoff material without making them executable truth |
