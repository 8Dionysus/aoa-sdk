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

R2 also publishes typing protocols for the control plane, AoARunner, and
runtime adapters. C1 implements `AoASDK.control_plane.resolve()` and
`.explain()` over an explicitly configured, receipt-bound canonical routing
snapshot. Construction remains lazy: it does not read the snapshot until
resolution. A selected route is candidate metadata only.

`AoASDK.control_plane.compile()` is implemented C2 behavior. It validates the
exact packaged `aoa-playbooks` contour/schema/trust pin and compiles an exact
`ScenarioBinding` plus runtime compatibility profile into a content-addressed
`RunPlan`. Construction remains lazy and compilation does not read the C1
routing snapshot.

`AoASDK.runner` is implemented C3 behavior. It prepares immutable sessions,
binds only a caller-supplied exact adapter profile, verifies runtime snapshot
observations before effectful transitions, and reconciles approvals, bounded
recovery, receipts, append-only events, status, outcomes, restore, and
closeout. The packaged reference adapter executes no plan steps. A production
runtime implementation and all model/tool execution remain outside the SDK.
The optional C4 `AbyssStackRuntimeAdapter` is a transport-only production
client: it materializes an exact owner profile from explicit artifacts and
uses one caller-supplied no-shell transport into the external runtime owner.

C5 adds `EvidenceChain` composition after the runtime outcome is immutable.
`assemble_evidence_chain()` accepts exact SDK control-plane objects and
external owner-qualified refs; `EvidenceChainRepository` stores immutable
content-addressed revisions and resolves only by exact session or final
closeout-receipt identity. Only a complete chain may close `AoARunner`.
Canonical eval, memo, checkpoint, and closeout payloads remain outside the SDK.

`AoASDK.organs` is a lazy facade over one explicitly configured private
registry source. It exposes deterministic projection, bounded catalog,
organ/capability inspection, compatibility comparison, and candidate-only
activation-plan compilation. Construction does not read the registry, scan
the workspace, connect to MCP, or execute an organ.
