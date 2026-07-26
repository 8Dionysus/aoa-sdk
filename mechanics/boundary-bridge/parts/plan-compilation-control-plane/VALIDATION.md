# Validation

Run:

```bash
python mechanics/boundary-bridge/parts/plan-compilation-control-plane/scripts/pin_playbook_plan_contours.py --owner-root /srv/AbyssOS/aoa-playbooks --check
python mechanics/boundary-bridge/parts/plan-compilation-control-plane/scripts/generate_plan_compilation_examples.py --check
python -m pytest -q mechanics/boundary-bridge/parts/plan-compilation-control-plane/tests
python -m build
python mechanics/boundary-bridge/parts/plan-compilation-control-plane/scripts/verify_plan_compilation_wheel.py
PATH_TO_VENV/bin/python mechanics/boundary-bridge/parts/plan-compilation-control-plane/scripts/verify_golden_scenario_chain.py --workspace /srv/AbyssOS/aoa-sdk
TMPDIR=/srv/abyss-machine/tmp/ai PATH_TO_VENV/bin/python mechanics/boundary-bridge/parts/plan-compilation-control-plane/scripts/verify_clean_federation_chain.py --source-federation /srv/AbyssOS --routing-bundle-root /srv/AbyssOS/abyss-stack/Knowledge/federation/aoa-routing
python -m mypy src/aoa_sdk/contracts/control_plane.py src/aoa_sdk/control_plane src/aoa_sdk/cli/route.py
python -m ruff check src/aoa_sdk/contracts/control_plane.py src/aoa_sdk/control_plane src/aoa_sdk/cli/route.py mechanics/boundary-bridge/parts/plan-compilation-control-plane
python scripts/validate_mechanics_topology.py
python scripts/validate_sdk_source_home.py
```

The three generated plans cover bounded-change preview pruning, A2A eval
without retention, and runtime proof handoff without source regrounding. A
fourth generated input bundle lets the installed-wheel probe reproduce the
bounded golden without importing the source checkout or requiring an
`aoa-playbooks` checkout. The installed-wheel golden-chain verifier uses only
the public SDK facade and public models to resolve, bind, and compile all three
scenarios from the exact live owner pins. It asserts explicit scenario
selection, repeatability, migration-backed capability identities, semantic
owner and availability visibility, and preservation of every unbound guard.
The clean-federation wrapper repeats that verifier with only the six required
owner repositories linked into a disposable federation and explicitly omits
an `aoa-routing` checkout.

The focused suite additionally covers repeatability, exact trust/source pins,
distinct trust-record logical and delivered-byte identities,
generic versus kind-selected inputs, no positional guessing, missing/extra
conditions, exact requirement refs, owner identity order, route snapshot
drift, absent selected scenario, migration-owner substitution, entry-route
versus contour separation, explicit versus contour-default approval step
bindings, standalone RunPlan parent-ref integrity, contour-to-ABI digest
identity, runtime effect compatibility, tampering, public API construction,
CLI compilation, and plan validation.

These checks do not activate or invoke a capability, instantiate a runner,
dispatch a runtime command, observe an execution event, prove task quality, or
establish cost reduction.
