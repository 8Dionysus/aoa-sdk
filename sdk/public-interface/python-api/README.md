# Python API Contract

Role: route the importable Python API posture.

Input: changes to `AoASDK`, exported SDK names, API construction, or public
consumer expectations.

Output: implementation route, test route, mechanic route, or stronger-owner
handoff.

Owner: `sdk/public-interface/AGENTS.md` and
`sdk/source_home.manifest.json#python_api_contract`.

Next route: `src/aoa_sdk/api.py`, `src/aoa_sdk/__init__.py`, public API tests,
and `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`.

Stop line: do not document an API promise here unless implementation and tests
carry it.

Artifact trust access is a typed consumer facade only. `AoASDK.artifacts` may
load and validate abyss-machine JSON surfaces such as trust-gate verdicts,
artifact classification, bundle registries, artifact requirements, affected
drift read-models, trust coverage, update-lane status, and update metadata
verification reports. Host enforcement, policy authority, evidence promotion,
and update client blocking decisions remain in `abyss-machine`.
