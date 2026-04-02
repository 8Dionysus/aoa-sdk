# aoa-sdk

Typed Python SDK for the AoA federation.

`aoa-sdk` is the local-first typed consumer and orchestration spine for source-owned AoA surfaces. It loads generated contracts from sibling repositories and exposes stable Python APIs for routing, skill discovery and activation, phase-aware artifacts, compatibility checks, and bounded orchestration without taking ownership away from the repositories that define meaning.

This repository was seeded from the `Dionysus` starter artifacts on 2026-03-31. It is now the live development home for the SDK itself.

## Start here

Use the shortest route by need:

- ownership and scope: `docs/boundaries.md`
- workspace topology and override rules: `docs/workspace-layout.md` and `.aoa/workspace.toml`
- compatibility posture: `docs/versioning.md`
- federation effects and obligations: `docs/ecosystem-impact.md`
- original seed blueprint: `docs/blueprint.md`
- local agent instructions: `AGENTS.md`

## Route by need

- machine-readable workspace and discovery alignment: `.aoa/workspace.toml`, `src/aoa_sdk/workspace/discovery.py`, and `docs/workspace-layout.md`
- source ownership and federation effects: `docs/boundaries.md` and `docs/ecosystem-impact.md`
- compatibility rules and local checks: `docs/versioning.md`, `aoa compatibility check /srv/aoa-sdk`, and `aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json`
- typed facade and downstream-consumer entrypoints: `src/aoa_sdk/`, `tests/`, and the example under `Current slice`
- local validation and workspace inspection: `aoa workspace inspect /srv/aoa-sdk`, `python -m pip install -e '.[dev]'`, and `pytest -q`

## What `aoa-sdk` owns

This repository is the source of truth for:

- typed loaders and facades over source-owned federation surfaces
- workspace discovery and topology resolution
- compatibility checks across consumed local surfaces
- bounded activation, disclosure, and orchestration helpers
- local CLI inspection surfaces that stay subordinate to source-owned meaning

## What it does not own

- It does not replace `aoa-routing`.
- It does not become the source of truth for skills, evals, memo, playbooks, agents, or KAG.
- It does not become a service runtime or hidden monolith.

The SDK stays on the control plane: load, type, validate, activate, and hand off.

## Current slice

```python
from aoa_sdk import AoASDK

sdk = AoASDK.from_workspace("/srv/aoa-sdk")

matches = sdk.routing.pick(kind="skill", query="bounded repo change")
preview = sdk.skills.disclose("aoa-change-protocol")
activation = sdk.skills.activate("aoa-change-protocol")
verify_binding = sdk.agents.binding_for_phase("verify")
playbook = sdk.playbooks.get("bounded-change-safe")
memory = sdk.memo.recall(mode="semantic", query="charter")
eval_bundle = sdk.evals.inspect("aoa-bounded-change-quality")
kag = sdk.kag.inspect("AOA-K-0011")
compatibility = sdk.compatibility.check_all()
```

The live read path already covers `aoa-routing`, `aoa-skills`, `aoa-agents`, `aoa-playbooks`, `aoa-memo`, `aoa-evals`, and bounded `aoa-kag` inspect support.

## Workspace topology

- the usual editable federation root is `/srv`
- `abyss-stack` is the important exception: the source checkout lives at `~/src/abyss-stack`
- `/srv/abyss-stack` is a deployed runtime mirror, not the preferred source checkout
- `.aoa/workspace.toml` is the machine-readable workspace manifest

## Local commands

Inspect the resolved workspace layout:

```bash
aoa workspace inspect /srv/aoa-sdk
aoa workspace inspect /srv/aoa-sdk --json
```

Check consumed surface compatibility across the local workspace:

```bash
aoa compatibility check /srv/aoa-sdk
aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json
```

Install for development and run tests:

```bash
python -m pip install -e '.[dev]'
pytest -q
```

## Downstream consumers

The SDK is intended for downstream consumers such as `ATM10-Agent`, local scripts, notebooks, CI helpers, and future adapters that need typed access to AoA surfaces without scattering parsing glue across multiple projects.
