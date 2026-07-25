# Release Audit Publish Helper

This part owns the SDK route from release surfaces to bounded audit and publish
helper behavior.

## Role

Input: changelog, current-release banner, package version files, local git
state, tags, GitHub Release state, and repo release route.

Output: preflight, postpublish, cadence, dry-run, and publish reports that
verify release state without inventing it.

Owner: `aoa-sdk` owns release helper API behavior, report shape, runbook route,
and tests. GitHub, package indexes, and owner repositories own actual release
state.

## Active Surfaces

- [Release Runbook](docs/release-runbook.md)
- [Release Audit Publish Helper Tests](tests/test_release_audit_publish_helper.py)
- `scripts/validate_abyss_machine_package_artifact_bundle.py`
- `scripts/build_routing_g5_release_candidate.py`
- `sdk/distribution/manifests/routing_g5_release_candidate.input-lock.json`
- `sdk/distribution/manifests/python_distribution.bundle.json`
- `src/aoa_sdk/release/`
- `scripts/release_check.py`
- `docs/RELEASING.md`
- `.github/workflows/release-artifacts.yml`
- `.github/workflows/release-cadence-audit.yml`

## Next Route

Route real publication through protected branch checks, tags, GitHub Release
verification, and package publication verification.

The package artifact helper must not stop at generated sidecars. It promotes
durable OS Abyss evidence with source and host-managed trust-root metadata,
confirms release-ready latest selection, materializes the package subject store,
checks consumer `trust-gate` admission, and rehearses missing SBOM, wrong SLSA
subject, private path leakage, unverified latest, and revoked-record denial
before a package carrier is trusted.

The routing release-candidate helper is a different route. It binds exact
source and verifier commits, builds a deterministic public archive, and checks
the release envelope with all 29 subjects byte-resolved through an explicit
runtime subject root, without promoting canonical routing authority. Public
release and stronger-owner records remain external truth.

Release-evidence replay is a bounded recovery route: the repaired workflow may
run from newer `main`, but package and producer source must be checked out from
the named existing immutable tag. Replay never authorizes a tag move or source
substitution.
