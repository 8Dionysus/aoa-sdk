# AGENTS.md

## Applies to

Everything under `stats/` in `aoa-sdk`.

## Role

This directory owns SDK-local statistical questions, their embedded
measurement contracts, and evidence-linked reference packets. Shared
statistical grammar and cross-owner composition remain owned by `aoa-stats`.

## Read before editing

1. Root `AGENTS.md`, `README.md`, and `DESIGN.md`.
2. `stats/README.md` and `stats/port.manifest.json`.
3. `docs/versioning.md` and `src/aoa_sdk/compatibility/policy.py`.
4. The central measurement and packet contracts under `aoa-stats/stats/`.

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

## Validation

Inspect the owner policy first:

```bash
PYTHONPATH=src python -c 'from aoa_sdk.compatibility.policy import SURFACE_COMPATIBILITY_RULES as rules; versioned=[key for key, rule in rules.items() if rule.version_field is not None]; unversioned=[key for key, rule in rules.items() if rule.version_field is None]; print({"population": len(rules), "versioned": len(versioned), "ratio": len(versioned) / len(rules), "unversioned": unversioned})'
```

Then validate the port and its packet with the central contract owner:

```bash
python scripts/validate_local_stats_port.py
```

## Closeout

Report the question or contract changed, the compatibility policy inspected,
whether the reference packet was refreshed, and which validation route ran.
