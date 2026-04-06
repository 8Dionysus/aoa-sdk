# aoa-sdk

Typed Python SDK for the AoA federation.

`aoa-sdk` is the local-first typed consumer and control-plane helper layer for source-owned AoA surfaces. It loads generated contracts from sibling repositories and exposes stable Python APIs for routing, skill discovery and activation, phase-aware artifact reads, compatibility checks, governed-run inspection, and other bounded control-plane helpers without taking ownership away from the repositories that define meaning.

This repository was seeded from the `Dionysus` starter artifacts on 2026-03-31. It is now the live development home for the SDK itself.

## Start here

Use the shortest route by need:

- ownership and scope: `docs/boundaries.md`
- workspace topology and override rules: `docs/workspace-layout.md` and `.aoa/workspace.toml`
- compatibility posture: `docs/versioning.md`
- reviewed session closeout orchestration: `docs/session-closeout.md`
- RPG typed consumer slice: `docs/RPG_SDK_ADDENDUM.md`, `docs/RPG_SURFACE_PATHS.md`, and `src/aoa_sdk/rpg/`
- federation effects and obligations: `docs/ecosystem-impact.md`
- seed blueprint and direction surface: `docs/blueprint.md`
- local agent instructions: `AGENTS.md`

## Route by need

- machine-readable workspace and discovery alignment: `.aoa/workspace.toml`, `src/aoa_sdk/workspace/discovery.py`, and `docs/workspace-layout.md`
- source ownership and federation effects: `docs/boundaries.md` and `docs/ecosystem-impact.md`
- compatibility rules and local checks: `docs/versioning.md`, `aoa compatibility check /srv/aoa-sdk`, and `aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json`
- typed facade and downstream-consumer entrypoints: `src/aoa_sdk/`, `tests/`, and the example under `Current slice`
- local validation and workspace inspection: `aoa workspace inspect /srv/aoa-sdk`, `aoa compatibility check /srv/aoa-sdk`, `python -m pytest -q`, and `python -m ruff check .`
- reviewed session closeout queue and reports: `docs/session-closeout.md`, `aoa closeout run`, and `aoa closeout process-inbox`
- reviewed session auto-closeout inbox: `docs/session-closeout.md`, `aoa closeout enqueue-current`, `aoa closeout status`, and `scripts/install_closeout_units.py`
- reviewed session manifest assembly: `docs/session-closeout.md` and `aoa closeout build-manifest`
- reviewed session request assembly from receipt bundles or audit-only reviewed artifacts: `docs/session-closeout.md` and `aoa closeout submit-reviewed`
- kernel-aware next-step brief after reviewed closeout: `docs/session-closeout.md`, `aoa closeout run`, and `aoa closeout process-inbox`
- project-core outer-ring structure and readiness: `sdk.skills.project_core_outer_ring()`, `sdk.skills.project_core_outer_ring_readiness()`, and the `aoa-skills` generated project-core ring surfaces
- project risk guard ring structure and governance: `sdk.skills.project_risk_guard_ring()`, `sdk.skills.project_risk_guard_ring_governance()`, and the `aoa-skills` generated risk-ring surfaces

## What `aoa-sdk` owns

This repository is the source of truth for:

- typed loaders and facades over source-owned federation surfaces
- workspace discovery and topology resolution
- compatibility checks across consumed local surfaces
- bounded activation, disclosure, and orchestration helpers
- reviewed-session closeout helpers that publish owner-local receipts and refresh live stats
- reviewed-session inbox automation that stays subordinate to reviewed manifests and owner-owned publishers
- canonical manifest assembly from reviewed artifacts and receipt paths, with optional audit-only reviewed closeout when no owner-local receipts exist yet
- canonical request assembly from reviewed artifacts plus receipt bundles before manifest/enqueue
- separate closeout routing for skill-detail receipts and generic project-core kernel skill-application receipts
- kernel-aware next-step brief generation based on `aoa-skills.project_core_skill_kernel.min` and refreshed `aoa-stats.core_skill_application_summary.min`
- typed readability for the static project-core engineering outer ring from `aoa-skills.project_core_outer_ring.min` and `aoa-skills.project_core_outer_ring_readiness.min`
- typed readability for the static project risk guard ring from `aoa-skills.project_risk_guard_ring.min` and `aoa-skills.project_risk_guard_ring_governance.min`
- local CLI inspection surfaces that stay subordinate to source-owned meaning

## What it does not own

- It does not replace `aoa-routing`.
- It does not become the source of truth for skills, evals, memo, playbooks, agents, or KAG.
- It does not become a service runtime or hidden monolith.

The SDK stays on the control plane: load, type, validate, activate, and hand off.

## Verify current repo state

Use this read-only/current-state battery:

```bash
python -m pytest -q
python -m ruff check .
aoa workspace inspect /srv/aoa-sdk
aoa compatibility check /srv/aoa-sdk
aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json
```

CI also reinforces this path with:

```bash
python -m mypy src
python -m build
```

## Current slice

```python
from aoa_sdk import AoASDK

sdk = AoASDK.from_workspace("/srv/aoa-sdk")

matches = sdk.routing.pick(kind="skill", query="bounded repo change")
preview = sdk.skills.disclose("aoa-change-protocol")
activation = sdk.skills.activate("aoa-change-protocol")
outer_ring = sdk.skills.project_core_outer_ring()
outer_ring_readiness = sdk.skills.project_core_outer_ring_readiness()
risk_ring = sdk.skills.project_risk_guard_ring()
risk_ring_governance = sdk.skills.project_risk_guard_ring_governance()
verify_binding = sdk.agents.binding_for_phase("verify")
playbook = sdk.playbooks.get("bounded-change-safe")
memory = sdk.memo.recall(mode="semantic", query="charter")
eval_bundle = sdk.evals.inspect("aoa-bounded-change-quality")
automation = sdk.stats.automation_pipelines("pipeline:session-growth")
kag = sdk.kag.inspect("AOA-K-0011")
rpg_build = sdk.rpg.latest_build("AOA-A-0002")
compatibility = sdk.compatibility.check_all()
```

The live read path already covers `aoa-routing`, `aoa-skills`, `aoa-agents`, `aoa-playbooks`, `aoa-memo`, `aoa-evals`, `aoa-stats`, and bounded `aoa-kag` inspect support.
The RPG addendum is also available as a typed consumer slice when its
canonical transport surfaces are present or fixture-staged.

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

Run one reviewed session closeout manifest:

```bash
aoa closeout run /srv/path/to/closeout.json --root /srv/aoa-sdk --json
```

Process the canonical closeout inbox:

```bash
aoa closeout process-inbox /srv/aoa-sdk --json
```

Queue one reviewed closeout manifest for automatic inbox processing:

```bash
aoa closeout submit-reviewed /srv/path/to/reviewed_session_artifact.md --session-ref session:2026-04-06-session-growth --receipt-dir /srv/path/to/receipts --root /srv/aoa-sdk --json
aoa closeout submit-reviewed /srv/path/to/W4-closeout.md --session-ref session:qwen-local-pilot-v1:W4:closeout --audit-ref /srv/path/to/W4-closeout.json --allow-empty --root /srv/aoa-sdk --json
aoa closeout build-manifest /srv/path/to/closeout.request.json --root /srv/aoa-sdk --enqueue --json
aoa closeout enqueue-current /srv/path/to/closeout.json --root /srv/aoa-sdk --json
aoa closeout status /srv/aoa-sdk --json
python scripts/install_closeout_units.py --overwrite --enable
```

Install for development:

```bash
python -m pip install -e '.[dev]'
```

## Downstream consumers

The SDK is intended for downstream consumers such as `ATM10-Agent`, local scripts, notebooks, CI helpers, and future adapters that need typed access to AoA surfaces without scattering parsing glue across multiple projects.
