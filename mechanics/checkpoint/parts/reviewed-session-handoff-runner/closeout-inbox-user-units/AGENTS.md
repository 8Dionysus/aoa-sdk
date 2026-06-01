# AGENTS.md

Local guidance for `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/`.
Read the root `AGENTS.md` and the reviewed-session handoff runner cards first.
This directory contains closeout inbox user unit templates for bounded SDK
helper flows.

## Scope

Current units such as `aoa-closeout-inbox.path` and `aoa-closeout-inbox.service` support explicit closeout-inbox processing.
They are deployment helpers, not proof that `aoa-sdk` owns runtime service doctrine.

## Local contract

- Keep units narrow, user-reviewable, and subordinate to documented SDK commands.
- Do not widen host exposure, add secret-bearing environment values, or assume private workstation paths.
- Prefer explicit paths, documented roots, and dry-run/report-only behavior where available.
- If a unit starts or watches a new surface, update docs, tests, and the validator map.
- Verify units syntactically before reporting success.

## Validate

Common gates:

```bash
systemd-analyze --user verify mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/aoa-closeout-inbox.path mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/aoa-closeout-inbox.service
python -m pytest -q
```
