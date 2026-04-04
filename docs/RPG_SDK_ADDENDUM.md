# RPG SDK Addendum

## Purpose

This note defines the narrow `aoa-sdk` addendum for typed loading of the five
canonical RPG contracts.

The SDK stays on the control plane. It loads, types, validates, filters, and
hands back stable Python objects.

It does not become the source of truth for the RPG layer.

## What this slice reads

In this pass the SDK reads:

- one vocabulary overlay from `Agents-of-Abyss`
- generated collections of build snapshots, reputation ledgers, quest run
  results, and frontend projection bundles from `abyss-stack`

## Why collection wrappers exist

The canonical runtime contracts are item-shaped.

The SDK needs list-friendly transport surfaces for discovery, filtering, and
helper selection.

So this pass expects thin generated collection wrappers such as:

- `agent_build_snapshot_collection_v1`
- `reputation_ledger_collection_v1`
- `quest_run_result_collection_v1`
- `frontend_projection_bundle_collection_v1`

These wrappers are transport conveniences only. They must not widen the
meaning of the underlying item contracts.

## Local compatibility posture

The SDK already has a repo-wide compatibility API for several AoA surfaces.

In this pass the RPG slice keeps its compatibility rules local under
`aoa_sdk.rpg.surfaces`.

This keeps the addendum narrow while the upstream generated file paths and
builders are still maturing.

A later promotion into the global compatibility registry is allowed if the
runtime transport paths become stable enough.

## API shape

The new public entrypoint is:

```python
from aoa_sdk import AoASDK

sdk = AoASDK.from_workspace("/srv/aoa-sdk")
overlay = sdk.rpg.vocabulary()
build = sdk.rpg.latest_build("AOA-A-0002")
ledger = sdk.rpg.ledger("AOA-A-0002")
run = sdk.rpg.run("QRR-2026-04-01-0001")
bundle = sdk.rpg.latest_bundle()
card = sdk.rpg.agent_sheet("AOA-A-0002")
```

## Boundary rules

- do not infer stronger doctrine than the loaded surfaces actually contain
- do not let frontend helpers hide source refs
- do not let helper methods mutate quest state or progression state
- do not collapse runtime budgets into metaphysical truth
- do not replace multi-axis progression with one score

## Orchestrator posture

Codex is the current primary orchestrator driver, but the SDK slice must remain
orchestrator-agnostic.

Read orchestrator fields as data, not doctrine.

## Final rule

`aoa-sdk` should make the RPG layer readable.

It must not start secretly authoring it.
