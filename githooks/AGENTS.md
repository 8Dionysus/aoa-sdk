# AGENTS.md

Local guidance for `githooks/` in `aoa-sdk`. Read the root `AGENTS.md` first.
This directory contains Git hook wrappers for checkpoint and boundary awareness.

## Scope

Hooks such as `post-commit`, `pre-push`, and `pre-merge-commit` are guardrails around active sessions.
They can preserve review pressure and boundary checks, but they must not become a hidden closeout runtime.

## Local contract

- Keep hooks active-session-only. If no active runtime session exists, the hook path must not create a new session just to emit checkpoint noise.
- A hook-created checkpoint may require semantic review, but hooks must never run closeout, promotion, harvest, push, or release logic.
- Keep boundary hooks fail-closed only for the documented pending-review cases.
- Prefer small shell wrappers that delegate to reviewed SDK commands.
- Do not add secrets, workstation-local paths, or repo-specific hacks that bypass documented config.

## Validate

Common gates:

```bash
aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv/AbyssOS --json
python -m pytest -q
```
