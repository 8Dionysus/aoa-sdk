# AGENTS.md

## Repository purpose

`aoa-sdk` is the typed Python SDK for the AoA federation.
It consumes source-owned surfaces from sibling repositories and exposes a local-first API layer.

## Workspace topology

- Treat the checked-out repositories as the editable source layer.
- The usual federation root is `/srv`, where `aoa-sdk`, `aoa-routing`, `aoa-skills`, `aoa-agents`, `aoa-playbooks`, `aoa-memo`, `aoa-evals`, `Dionysus`, and related repositories live as peer directories.
- `abyss-stack` is the important exception: the git checkout lives at `~/src/abyss-stack`.
- `/srv/abyss-stack` is a deployed runtime mirror, not the source checkout.
- If both paths exist, prefer editing `~/src/abyss-stack`.

## Source of truth for topology

- `.aoa/workspace.toml` is the machine-readable workspace manifest for this repository.
- `docs/workspace-layout.md` explains the topology and override rules for humans.
- `src/aoa_sdk/workspace/discovery.py` must stay aligned with both.

## Editing guidance

- Keep workspace discovery explicit and reviewable.
- Prefer config and manifest-driven behavior over one-off path heuristics.
- When changing topology behavior, update tests and docs in the same change.
- Preserve the distinction between source checkouts and runtime mirrors.

## Validation

- `python -m pytest -q`
- `python -m ruff check .`
- `aoa workspace inspect /srv/aoa-sdk`
