# Validation

Run:

```bash
python -m pytest -q mechanics/runtime-seam/parts/abyss-stack-runtime-adapter/tests
python -m pytest -q mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/tests
python -m ruff check src/aoa_sdk/runtime_adapters mechanics/runtime-seam/parts/abyss-stack-runtime-adapter
python -m mypy src/aoa_sdk/runtime_adapters
python mechanics/runtime-seam/parts/abyss-stack-runtime-adapter/scripts/verify_abyss_stack_adapter_wheel.py
python scripts/validate_mechanics_topology.py
python scripts/validate_sdk_source_home.py
```

The focused suite proves owner-descriptor and constraint hashing, exact
binding admission, missing/extra snapshot location rejection, typed Runner
delegation through a transport double, no-shell subprocess argument shape,
response-version checking, and transport-error closure.

Real runtime execution proof remains paired with the runtime owner at
`repo:abyss-stack/mechanics/governed-execution/parts/agent-os-adapter/tests`.
An SDK-only green suite or installed-wheel probe is not invocation proof.
