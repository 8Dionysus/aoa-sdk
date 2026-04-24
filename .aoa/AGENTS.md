# AGENTS.md

Local guidance for `.aoa/` in `aoa-sdk`. Read the root `AGENTS.md` first.
This directory carries workspace topology metadata for the SDK control plane.

## Scope

`.aoa/workspace.toml` describes how the SDK resolves sibling repositories and local workspace expectations.
It is configuration for explicit discovery, not a hidden source of truth for repo meaning.

## Local contract

- Keep `.aoa/workspace.toml`, `docs/workspace-layout.md`, and `src/aoa_sdk/workspace/discovery.py` aligned.
- Prefer explicit config over no hidden path guessing.
- Preserve the split between source checkouts and runtime mirrors: /srv/abyss-stack is a deployed runtime mirror, not the preferred source checkout.
- Keep `/srv` assumptions documented and overrideable.
- Do not add machine-local secrets, private paths, or unreviewable heuristics.

## Validate

Common gates:

```bash
aoa workspace inspect /srv/aoa-sdk
python -m pytest -q
```
