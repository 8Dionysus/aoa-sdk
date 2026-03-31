# aoa-sdk

Typed Python SDK for the AoA federation.

`aoa-sdk` is the local-first typed consumer and orchestration spine for
source-owned AoA surfaces. It loads generated contracts from sibling
repositories and exposes stable Python APIs for routing, skill discovery and
activation, phase-aware artifacts, and bounded orchestration without taking
ownership away from the repositories that define meaning.

This repository was seeded from the `Dionysus` starter artifacts on
2026-03-31 and should now become the live development home for the SDK itself.

## Role In The Federation

- Provide one Python entrypoint for downstream consumers such as ATM10-Agent,
  local scripts, notebooks, CI helpers, and future adapters.
- Keep typed loaders, policy-aware wrappers, and orchestration helpers in one
  place instead of scattering parsing glue across multiple consumers.
- Stay on the control plane: load, type, validate, activate, and hand off.

## What This Repository Does Not Own

- It does not replace `aoa-routing`.
- It does not become the source of truth for skills, evals, memo, playbooks,
  or agents.
- It does not become a service runtime or hidden monolith.

## Seed Contents

- `src/aoa_sdk/` - initial scaffold for the public Python package
- `docs/blueprint.md` - the original seed blueprint carried over from
  `Dionysus`
- `docs/boundaries.md` - compact ownership rules for keeping the SDK narrow
- `docs/ecosystem-impact.md` - immediate effects, obligations, and risks added
  by the new repository

## Status

- initial scaffold only
- local filesystem loading first
- typed read path before orchestration depth

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
```
