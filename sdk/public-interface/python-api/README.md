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
