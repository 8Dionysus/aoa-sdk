# Changelog

All notable changes to `aoa-sdk` will be documented in this file.

The format is intentionally simple and human-first.

## [Unreleased]

## [0.2.0] - 2026-04-10

### Summary

- this release adds a workspace control-plane capsule, first-class checkpoint lanes, closeout bridging, and thread-aware Codex session tracing
- checkpoint typing, registry guardrails, actor references, local-time reporting, and control-plane validation are hardened across CLI and generated outputs
- `aoa-sdk` remains the typed control-plane and orchestration layer rather than a runtime owner

### Validation

- `python scripts/release_check.py`

### Notes

- detailed source, schema, generated-surface, and operator-surface coverage for this release remains enumerated below under `Added`, `Changed`, and `Included in this release`

### Added

- workspace control-plane capsule plus compatibility tracking for center/root
  entry capsules and routing/stats ABI v2
- a first-class checkpoint lane with auto-captured skill-phase and
  commit-growth checkpoints, progression carry-through, and closeout execution
  bridging
- thread-aware Codex session tracing and runtime-identity scoping for
  checkpoint closeout

### Changed

- hardened checkpoint typing, registry guardrails, actor refs, and local-time
  reporting across CLI and generated outputs
- expanded docs, tests, and dev extras around checkpoint closeout and
  control-plane validation

### Included in this release

- control-plane and typed-consumer expansion across `src/`, `schemas/`,
  `generated/`, `scripts/`, and `systemd/`, including RPG and `aoa-stats`
  consumer slices, reviewed closeout submission flows, closeout publishers and
  watchers, surface detection, and the workspace control-plane capsule
- workspace, checkpoint, and operator surfaces across `docs/`, `README.md`,
  `AGENTS.md`, `.agents/`, `.github/`, `tests/`, and `pyproject.toml`,
  including portable bootstrap and ingress wrappers, foundation skill
  detection, via negativa and antifragility doctrine, and thread-aware
  checkpoint-closeout hardening

## [0.1.0] - 2026-04-01

First public baseline release of `aoa-sdk` as the typed Python SDK for the AoA federation.

This changelog entry uses the release-prep merge date.

### Summary

- first public baseline release of `aoa-sdk` as the local-first typed consumer and orchestration spine for source-owned AoA surfaces
- the live read path now covers `aoa-routing`, `aoa-skills`, `aoa-agents`, `aoa-playbooks`, `aoa-memo`, `aoa-evals`, and bounded `aoa-kag` inspect support
- the release also ships workspace discovery, source-checkout versus runtime-mirror topology handling, compatibility checks, skill session helpers, and CLI inspection surfaces

### Added

- seeded the repository from the initial `Dionysus` `aoa-sdk` starter artifacts
- the first package scaffold, boundary docs, workspace layout docs, versioning docs, and ecosystem impact docs
- the first live local-first read path to `aoa-routing`, `aoa-skills`, and `aoa-agents`
- sibling workspace discovery, typed surface loaders, skill session helpers, and isolated fixture-based tests
- the extended local-first read path to `aoa-playbooks`, `aoa-memo`, and `aoa-evals`
- an explicit per-surface compatibility policy, including versioned and versionless surface handling
- a tracked workspace manifest, environment overrides, and CLI inspection for source-checkout versus runtime-mirror topology

### Changed

- workspace discovery now prefers the git source checkout at `~/src/abyss-stack` over the deployed runtime mirror at `/srv/abyss-stack`
- package and CLI version surfaces are now aligned to `0.1.0` for the first repository release

### Validation

- `pytest -q`
- `python -m ruff check .`
- `aoa workspace inspect /srv/aoa-sdk`

### Notes

- this release keeps `aoa-sdk` on the control plane: typed loading, disclosure, compatibility, activation, and handoff helpers rather than runtime ownership
