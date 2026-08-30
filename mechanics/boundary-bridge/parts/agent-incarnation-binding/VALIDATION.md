# Validation

Run:

```bash
python mechanics/boundary-bridge/parts/agent-incarnation-binding/scripts/generate_agent_incarnation_schema.py --check
python -m pytest -q mechanics/boundary-bridge/parts/agent-incarnation-binding/tests
python -m ruff check src/aoa_sdk/contracts/incarnation.py src/aoa_sdk/contracts/delegation.py src/aoa_sdk/control_plane/incarnation.py src/aoa_sdk/runtime_adapters mechanics/boundary-bridge/parts/agent-incarnation-binding
python -m mypy src/aoa_sdk/contracts/incarnation.py src/aoa_sdk/control_plane/incarnation.py src/aoa_sdk/runtime_adapters/abyss_stack.py
python scripts/validate_mechanics_topology.py
python scripts/validate_sdk_source_home.py
```

The focused tests prove byte-stable v1 compatibility, required v2 obligation,
mandate, role-resolution, fit-result and fit-projection binding, digest and
owner separation, exact runtime-subject binding and tamper rejection, exact
plan/task/role matching, continuation completeness,
exact continuity-capsule carry through plan, binding, session, and resume,
effect ceilings, model-record hashing, runtime-profile owner projection, stale
plan-digest rejection, and generated v1/v2 schema parity. Runtime execution
remains paired proof in `abyss-stack`. Delegation-class tests additionally
prove the discriminated `ephemeral_read_worker_v1` and
`external_incarnation_v1` ABI, parent-retained versus transferred responsibility,
owner-separated runtime/eval/closeout/acceptance refs, and adapter neutrality.
The delegation-class tests are the focused source contract for this distinction.
