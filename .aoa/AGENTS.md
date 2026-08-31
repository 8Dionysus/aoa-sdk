# AGENTS.md

Local guidance for `.aoa/` in `aoa-sdk`. Read the root `AGENTS.md` first.
This directory carries workspace topology metadata for the SDK control plane.

## Scope

`.aoa/workspace.toml` describes how the SDK resolves sibling repositories and local workspace expectations.
It is configuration for explicit discovery, not a hidden source of truth for repo meaning.

## Local contract

- Keep `.aoa/workspace.toml`, `docs/workspace-layout.md`, and `src/aoa_sdk/workspace/discovery.py` aligned.
- Prefer explicit config over no hidden path guessing.
- Preserve the split between source checkouts and runtime mirrors:
  /srv/AbyssOS/abyss-stack is a deployed runtime mirror, not the preferred source
  checkout.
- Keep `/srv` assumptions documented and overrideable.
- Do not add machine-local secrets, private paths, or unreviewable heuristics.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.
