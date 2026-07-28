# Runner Entrypoints

Role: route the public lifecycle client below runtime execution authority.

Input: `AoASDK.runner`, `AoARunner`, runtime-adapter protocol, session
restoration, lifecycle commands, reference-adapter posture, an explicit
runtime-owner transport client, or evidence-chain closeout.

Output: Runner implementation, C3 mechanic, C4 transport-client route, C5
evidence-chain route, production runtime-owner handoff, or versioned contract
decision.

Owner: `sdk/runtime-entry/AGENTS.md` and
`sdk/source_home.manifest.json#runner_entrypoints`.

Next route: `src/aoa_sdk/control_plane/runner/`,
`src/aoa_sdk/contracts/control_plane.py`, `src/aoa_sdk/runtime_adapters/`,
`mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/`, and
`mechanics/runtime-seam/parts/abyss-stack-runtime-adapter/`, or
`mechanics/boundary-bridge/parts/evidence-closeout-chain/`.

Stop line: the SDK coordinates and verifies lifecycle state through one
caller-supplied adapter. It does not discover an adapter, execute a plan step,
run a model or tool, or turn the deterministic reference adapter into
production execution evidence. An installed transport client is not proof
that the runtime-owner bridge was invoked.

For C5, the Runner accepts closeout only from a complete immutable
`EvidenceChain`. The SDK may validate cross-owner identity and completeness;
it must not mint eval verdicts, memo contents, checkpoint receipts, or
closeout payloads.
