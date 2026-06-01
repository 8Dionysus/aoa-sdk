# Public Support Sibling Canary Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0031
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, ci
- SDK facets: mechanics topology, release support, compatibility, public support
- Mechanic parents: release-support
- Guard families: root-surface hygiene, compatibility drift, active naming
- Posture: accepted

## Context

The sibling canary script and matrix were still in root `scripts/`, with their
regression in root `tests/`.

The actual operation is narrower than repo-wide scripting: it is Tier 3 public
support and CI posture. It verifies live sibling compatibility drift for the
claims described by `public-support-ci-posture`.

## Decision

Move the sibling canary surfaces into the owning part:

- `mechanics/release-support/parts/public-support-ci-posture/config/sibling_canary_matrix.json`
- `mechanics/release-support/parts/public-support-ci-posture/scripts/run_sibling_canary.py`
- `mechanics/release-support/parts/public-support-ci-posture/tests/test_sibling_canary.py`

Update the scheduled GitHub workflow, README route, versioning posture, part
cards, topology map, and artifact ledger to reference the part-local route.

## Rationale

Root `scripts/` should keep repo-wide validators, release gates, shared
builders, and truly cross-mechanic operator utilities. A sibling canary matrix
is a public support CI posture artifact: it exists to keep support claims
honest against sibling compatibility drift.

The active path should therefore say the operation, owner, artifact kind, and
validation route directly.

## Consequences

- Root `scripts/` no longer carries sibling-canary public-support payload.
- Root `tests/` no longer carries the sibling-canary regression.
- `.github/workflows/latest-sibling-canary.yml` calls the part-local runner.
- Public docs route canary changes through `public-support-ci-posture`.

## Source Surfaces

- `mechanics/release-support/parts/public-support-ci-posture/config/sibling_canary_matrix.json`
- `mechanics/release-support/parts/public-support-ci-posture/scripts/run_sibling_canary.py`
- `mechanics/release-support/parts/public-support-ci-posture/tests/test_sibling_canary.py`
- `.github/workflows/latest-sibling-canary.yml`
- `.github/CODEOWNERS`
- `mechanics/release-support/parts/public-support-ci-posture/docs/public-support-ci-posture.md`
- `docs/versioning.md`
- `README.md`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`

## Follow-Up Route

Keep future live sibling drift checks under the public-support CI posture part
unless they become a repo-wide release gate with a separate release-support
decision and validator.

## Verification

```bash
python -m pytest -q mechanics/release-support/parts/public-support-ci-posture/tests/test_sibling_canary.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py tests/test_docs_routes.py
python mechanics/release-support/parts/public-support-ci-posture/scripts/run_sibling_canary.py --repo-root . --repo aoa-skills --format json
python scripts/validate_mechanics_topology.py
```
