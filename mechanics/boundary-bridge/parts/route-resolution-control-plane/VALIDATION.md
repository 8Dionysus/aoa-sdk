# Validation

Repository-wide source-home, workspace-capsule, package-build, release, and full-suite checks are owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks) and [its release-facing lane](../../../../VALIDATION.md#release-facing-and-full-owner-checks).

Run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/route-resolution-control-plane/tests
python -m mypy src/aoa_sdk/control_plane src/aoa_sdk/cli/route.py
python -m ruff check src/aoa_sdk/control_plane src/aoa_sdk/cli/route.py
```

The focused suite covers repeatability, no predecessor checkout, exact
top-rank ambiguity blocking, deferred capability gating, negative
applicability, unsupported and conflicting constraints, bundle tampering,
source-lock owner binding, cross-owner projection mismatch, public CLI chain,
and lazy facade construction.

For a live smoke, point `AOA_SDK_ROUTING_BUNDLE_ROOT` at the deployed
SDK-canonical `abyss-stack` mirror and resolve a bounded `RouteIntent`.
Record the selected candidate, candidate count, snapshot digest, and
`fallback_used=false`.

These checks do not prove plan compilation, capability invocation, runtime
execution, task quality, process cost, or compatibility-window exit.

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
