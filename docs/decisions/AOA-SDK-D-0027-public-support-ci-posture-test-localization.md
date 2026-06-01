# Public Support CI Posture Test Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0027
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, release support, public support posture
- Mechanic parents: release-support
- Guard families: mechanics topology, part validation, docs routes, active naming
- Posture: accepted

## Context

After release-support payload localization, the public support posture
regression still lived as a root test named `tests/test_roadmap_parity.py`.
That name described one old symptom, not the active owner surface: public
support, release-claim, and CI posture must remain aligned with README,
ROADMAP, changelog, and the workspace control-plane capsule.

## Decision

Move the regression into:

- `mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py`

Keep root `tests/test_docs_routes.py` as a repo-wide docs route validator.
The former root test path is provenance only.

## Rationale

The active part name now tells an agent what the surface does: it checks
whether public support claims, release semantics, CI posture, and current
control-plane routes remain mutually legible. `roadmap parity` is a useful
historical symptom, but it is too narrow and should not be the active route
name.

## Consequences

- Release-support validation routes through the part-local posture test.
- Broader Codex Projection and Experience validation notes that need the same
  posture check now call the part-local test path.
- Root `tests/` no longer carries this single-mechanic release-support
  regression.

## Source Surfaces

- `mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py`
- `mechanics/release-support/parts/public-support-ci-posture/VALIDATION.md`
- `mechanics/release-support/README.md`
- `mechanics/release-support/PROVENANCE.md`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `docs/decisions/AOA-SDK-D-0018-release-support-part-localization.md`

## Follow-Up Route

Continue the root test audit and move remaining mechanic-owned CLI, bootstrap,
and SDK facade tests into their owning parts while keeping repo-wide validators
at root.

## Verification

```bash
python -m pytest -q mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py tests/test_docs_routes.py
python scripts/validate_mechanics_topology.py
python scripts/generate_decision_indexes.py --check
```
