# Documentation Map

This is the entrypoint for the `docs/` surface of `aoa-sdk`.

Use the root [README](../README.md) as the public front door. Use this file
after entering `docs/` to choose the boundary, workspace, versioning, release,
seed-history, or decision surface without guessing from filenames.

Operational edit law belongs in the nearest `AGENTS.md`. This map explains
where meaning lives and which surface to open next.

## Operating Card

| Field | Route |
| --- | --- |
| role | docs entrypoint and source-of-truth chooser |
| input | boundary, workspace, compatibility, release, docs-placement, seed-history, or decision-rationale question |
| output | next source surface, mechanic route, decision record, or stronger-owner stop line |
| owner | `docs/AGENTS.md` for docs edits; target source files own their meaning |
| next route | root `README.md`, `DESIGN.md`, `DESIGN.AGENTS.md`, `docs/decisions/`, `mechanics/`, or sibling owner repositories |
| validation | [docs/AGENTS](AGENTS.md) and the nearest owner route card |

## First Route

| Question | Open |
| --- | --- |
| What is this repository? | [aoa-sdk](../README.md) |
| May this claim live in the SDK? | [boundaries](boundaries.md), then [DESIGN](../DESIGN.md) |
| What is the current SDK direction? | [ROADMAP](../ROADMAP.md) |
| What is the docs edit route? | [docs AGENTS](AGENTS.md) |
| How does workspace discovery resolve source checkouts and mirrors? | [workspace layout](workspace-layout.md), then [.aoa workspace](../.aoa/workspace.toml) |
| What compatibility posture applies to consumed sibling surfaces? | [versioning](versioning.md) |
| How does release posture route? | [release route](RELEASING.md), [release and CI posture](RELEASE_CI_POSTURE.md), then [release-support mechanic](../mechanics/release-support/README.md) |
| Why was a route chosen? | [decision records](decisions/README.md) |
| What is old seed context rather than current authority? | [blueprint](blueprint.md) |

## Source Families

| Family | Owner Surface |
| --- | --- |
| Repository boundary and stronger-owner stop lines | [boundaries](boundaries.md) |
| Workspace topology and mirror rules | [workspace layout](workspace-layout.md) |
| Compatibility policy for consumed surfaces | [versioning](versioning.md) |
| Release preflight and public support posture | [RELEASING](RELEASING.md), [RELEASE_CI_POSTURE](RELEASE_CI_POSTURE.md), then release-support parts |
| Seed blueprint and bootstrap history | [blueprint](blueprint.md) |
| Structural rationale | [decisions](decisions/README.md) |

## Mechanic Routes

Mechanic-local docs live with their mechanics, not as a flat `docs/` pile.

| Pressure | Route |
| --- | --- |
| Release audit, publication helpers, CI posture, or sibling canaries | [release-support](../mechanics/release-support/README.md) |
| Workspace roots, mirrors, bootstrap, or control-plane capsule | [runtime-seam](../mechanics/runtime-seam/README.md) |
| Compatibility gates, sibling facades, skill bridges, or owner-layer handoff | [boundary-bridge](../mechanics/boundary-bridge/README.md) |
| Checkpoint capture, reviewed carry, closeout, or child-task re-entry | [checkpoint](../mechanics/checkpoint/README.md) |
| Codex MCP, rollout status, portability boundary, or rollout refs | [codex-projection](../mechanics/codex-projection/README.md) |
| Source quest records and quest reader posture | [questbook](../mechanics/questbook/README.md) |

## Change Routes

| Change | First route |
| --- | --- |
| Root or docs-map wording | [docs AGENTS](AGENTS.md), [DESIGN.AGENTS](../DESIGN.AGENTS.md), then this map |
| Boundary, workspace, or compatibility meaning | target doc, [DESIGN](../DESIGN.md), owning source/tests, and relevant mechanic |
| Release-visible public docs | [RELEASING](RELEASING.md), [RELEASE_CI_POSTURE](RELEASE_CI_POSTURE.md), release-support part, and [CHANGELOG](../CHANGELOG.md) when release notes are actually needed |
| Decision rationale | [decisions AGENTS](decisions/AGENTS.md), then [decisions README](decisions/README.md) |
| Mechanic-owned payload docs | [mechanics](../mechanics/README.md), then package `AGENTS.md`, `README.md`, `ROADMAP.md`, `PARTS.md`, and part `VALIDATION.md` |

## Topology Rule

`docs/` is not a flat shelf for old root guidance, one-off impact prose, or
single-mechanic payload. Current docs stay here only when they are repo-wide,
public-route, boundary, workspace, versioning, release-door, seed-history, or
decision-rationale surfaces.

Historical seed material must identify itself as history. Current operational
law belongs in the nearest active route card or mechanic part, not in preserved
root dumps.

## Notes

- Prefer the nearest owner route over adding another root paragraph.
- Prefer [decisions](decisions/README.md) when future contributors need the
  rationale for a topology or route-law choice.
- Prefer generated decision indexes for lookup. Do not hand-maintain a latest
  decision roster in prose.
