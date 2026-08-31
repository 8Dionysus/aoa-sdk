# AGENTS.md

## Applies to

Everything under `stats/` in `aoa-sdk`.

## Role

This directory owns SDK-local statistical questions, their embedded
measurement contracts, and evidence-linked reference packets. Shared
statistical grammar and cross-owner composition remain owned by `aoa-stats`.

## Relevant routes

The conditional references retained from this card are: `AGENTS.md`, `README.md`, `DESIGN.md`, `stats/README.md`, `stats/port.manifest.json`, `docs/versioning.md`, `src/aoa_sdk/compatibility/policy.py`, `aoa-stats/stats/`.

## Boundaries

- `port.manifest.json` owns the SDK-local question and measurement meaning.
- Reference packets are derived snapshots and remain weaker than the SDK
  compatibility policy and versioning posture.
- The version-negotiation ratio describes declared SDK compatibility posture
  only. It is not evidence that a sibling surface exists, is fresh, is
  semantically compatible, or is used successfully.
- Keep packet refs repository-relative and raw sibling payloads out of packets.
- Keep the typed sibling stats facade under `src/aoa_sdk/stats/`; it is a
  consumer boundary and is not this owner-local stats port.

## Closeout

Report the question or contract changed, the compatibility policy inspected,
whether the reference packet was refreshed, and which validation route ran.
