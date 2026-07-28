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

Configure the canonical bundle either with
`AOA_SDK_ROUTING_BUNDLE_ROOT` or with the workspace manifest:

```toml
[control_plane]
routing_bundle_root = "{workspace_parent}/abyss-stack/Knowledge/federation/aoa-routing"
```

The packaged canonical source lock is used unless
`AOA_SDK_ROUTING_SOURCE_LOCK` or
`control_plane.routing_source_lock` supplies an explicit rehearsal override.
The public control-plane models are exported from `aoa_sdk.models`:

```python
from datetime import datetime, timezone
import hashlib

from aoa_sdk import AoASDK
from aoa_sdk.models import AgentRef, ProvenanceRef, RouteIntent

objective = "find a durable repository decision and rationale"
objective_digest = "sha256:" + hashlib.sha256(objective.encode()).hexdigest()
caller_provenance = ProvenanceRef(
    owner_repo="agent-session",
    artifact_ref="intents/example-route-intent.json",
    source_ref="local-example",
    artifact_digest=objective_digest,
    schema_ref="aoa_control_plane_v1",
    schema_version="aoa_control_plane_v1",
)
intent = RouteIntent(
    intent_id="intent:example",
    correlation_id="correlation:example",
    objective=objective,
    requested_by=AgentRef(
        agent_id="example-caller",
        provenance=caller_provenance,
    ),
    requested_capability_kinds=("skill",),
    authored_at=datetime.now(timezone.utc),
    provenance=caller_provenance,
)

sdk = AoASDK.from_workspace("/path/to/federation/aoa-sdk")
decision = sdk.control_plane.resolve(intent)
explanation = sdk.control_plane.explain(decision)

print(decision.status, decision.selected_candidate_id)
print(explanation.fallback_used)
```

The caller must inspect `status`, selected-candidate compatibility, reason
codes, and approval requirements before any separate activation route. A
`degraded` decision is not silently promoted to `resolved`. Adding
`compatibility_requirement=compatible` can intentionally turn a
challenger-only result into `blocked`; use `degraded_allowed` only when the
caller is prepared to preserve that weaker posture.

`RouteIntent.requested_by` is the caller. Resolver v3 leaves
`RouteCandidate.agent` unset because C1 has no exact provider-agent projection;
scenario participants are resolved separately from `aoa-agents` during C2
binding.

`AoASDK.control_plane.scenario_ref()` and `.bind_scenario()` are implemented
C2 construction behavior. The caller first includes the exact scenario in the
intent; after resolution, the binder uses the same validated C1 snapshot to
resolve the admitted playbook's agents, capability aliases, eval refs, and
memo refs from exact pinned owner Git objects:

```python
from aoa_sdk.models import ScenarioConditionBinding

scenario = sdk.control_plane.scenario_ref("bounded_change_safe")
scenario_intent = intent.model_copy(
    update={
        "intent_id": "intent:example:bounded-change",
        "correlation_id": "correlation:example:bounded-change",
        "scenario": scenario,
    }
)
decision = sdk.control_plane.resolve(scenario_intent)
binding = sdk.control_plane.bind_scenario(
    decision,
    scenario.scenario_id,
    binding_id="scenario-binding:example:bounded-change",
    provenance=caller_provenance,
    input_refs=(caller_provenance,),
    condition_bindings=(
        ScenarioConditionBinding(
            condition_id="preview_required",
            value=False,
            provenance=caller_provenance,
        ),
    ),
)
plan = sdk.control_plane.compile(decision, binding, runtime_profile)
```

Here `runtime_profile` is an exact compatibility projection supplied by its
runtime owner. A consumer validates that owner payload through the public
model rather than inventing runtime policy:

```python
from aoa_sdk.models import RuntimeProfile

runtime_profile = RuntimeProfile.model_validate(runtime_owner_payload)
```

The required payload fields are `profile_id`, `runtime_owner`, `adapter_id`,
`supported_plan_schema_versions`, `supported_event_schema_versions`,
`supported_effect_classes`, and owner-matching `provenance`; the adapter
protocol defaults to `aoa_runtime_adapter_v1`. This declaration proves
compatibility only. It is not adapter selection, authorization, or execution.

The route entry capability remains decision metadata; playbook requirements
are independently mapped to current capability graph nodes with semantic
owner, availability, lifecycle, and migration provenance. Those nested fields
are inspected explicitly:

```python
for resolved in binding.capability_bindings:
    print(
        resolved.requirement_id,
        resolved.capability.capability_id,
        resolved.semantic_owner_repo,
        resolved.availability,
        resolved.lifecycle_health,
    )

print(plan.provenance.schema_version)  # compiler behavior version
```

`AoASDK.control_plane.compile()` validates the exact packaged
`aoa-playbooks` contour/schema/trust pin and compiles that binding plus the
runtime profile into a content-addressed `RunPlan`. Compilation itself does
not read the C1 routing snapshot and never activates the bound capabilities.
The fully executable installed-wheel route is
`mechanics/boundary-bridge/parts/plan-compilation-control-plane/scripts/verify_golden_scenario_chain.py`.

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
