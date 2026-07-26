# Runner Entrypoints

Role: route the public lifecycle client below runtime execution authority.

Input: `AoASDK.runner`, `AoARunner`, runtime-adapter protocol, session
restoration, lifecycle commands, or reference-adapter posture.

Output: Runner implementation, C3 mechanic, production runtime-owner handoff,
or versioned contract decision.

Owner: `sdk/runtime-entry/AGENTS.md` and
`sdk/source_home.manifest.json#runner_entrypoints`.

Next route: `src/aoa_sdk/control_plane/runner/`,
`src/aoa_sdk/contracts/control_plane.py`, and
`mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/`.

Stop line: the SDK coordinates and verifies lifecycle state through one
caller-supplied adapter. It does not discover an adapter, execute a plan step,
run a model or tool, or turn the deterministic reference adapter into
production execution evidence.
