# Routing Succession R1 Target Operating Model

Status: G1 accepted target; producer authority is not switched.

Machine-readable contract:
[`../evidence/routing-succession-r1-target-operating-model.json`](../evidence/routing-succession-r1-target-operating-model.json).

Durable SDK decision:
[`AOA-SDK-D-0071`](../../../../../docs/decisions/AOA-SDK-D-0071-staged-routing-producer-succession.md).

Paired predecessor decision:
`aoa-routing:docs/decisions/AOA-RT-D-0004-stage-producer-succession-to-aoa-sdk.md`.

## Accepted Outcome

`aoa-sdk` will inherit the routing producer and routing ABI through a staged,
receipt-bearing succession. It will become the AoA control plane for:

```text
RouteIntent
  -> RouteDecision
  -> RouteExplanation
  -> ScenarioBinding
  -> runtime-neutral RunPlan
  -> AoARunner lifecycle
```

This R1 landing accepts that outcome but does not make it live.
`aoa-routing` remains the canonical producer until shadow parity passes and an
explicit G5 owner-switch receipt names the source refs, ABI, artifacts,
runtime mirror, trust admission, and rollback route.

## State Model

| State | Canonical producer | Runnable implementations | Predecessor posture |
| --- | --- | ---: | --- |
| `predecessor_canonical` | `aoa-routing` | 1 | active owner |
| `sdk_shadow` | `aoa-routing` | 2 | active owner; SDK cannot publish |
| `sdk_canonical` | `aoa-sdk` | 1 | compatibility and rollback only |
| `archive_ready` | `aoa-sdk` | 1 | consumer-zero historical surface |
| `archived` | `aoa-sdk` | 1 | only after exact operator approval |

The measured transition is therefore:

```text
canonical owners:          1 -> 1
runnable implementations:  1 -> 2 (shadow) -> 1
active repo control planes: 2 -> 1
```

## Authority Matrix

| Operation | Authority owner | SDK role | Stop line |
| --- | --- | --- | --- |
| discover | source organ named by the object reference | compatibility-checked discovery with provenance | presence is not selection or activation |
| choose candidate | SDK control plane after G5 | explicit ranking under owner constraints | candidate is not authorization |
| resolve candidate | SDK control plane after G5 | deterministic decision and structured explanation | resolution is not execution |
| authorize candidate | operator or policy authority named by `ApprovalRequirement` | carry request and decision | SDK cannot infer or bypass approval |
| activate candidate | selected runtime owner | request through negotiated adapter | Runner is not an activation body |
| execute candidate | selected runtime owner | consume events and coordinate lifecycle | SDK core executes no model or tool |
| evaluate result | `aoa-evals` or stronger proof owner | correlate evidence and verdict refs | runtime success is not verdict |
| retain result | `aoa-memo` or selected session-memory owner | carry request and receipt refs | no canonical memory copy in SDK |
| close session | SDK lifecycle control plane | verify terminal prerequisites and assemble `CloseoutBundleRef` | lifecycle closure does not replace runtime termination, proof, or retention |

The machine-readable contract separately names source, projection, route,
policy, approval, activation, execution, evidence, verdict, memory, and
closeout ownership. Where one lifecycle step touches several artifacts, each
artifact retains a distinct owner instead of sharing an ambiguous label.

## Artifact Compatibility

The owner-only switch preserves:

- all fourteen current root output paths;
- `aoa_routing_thin_router_v1`;
- supported schema identifiers and payload meaning;
- normal consumer precedence and compatibility behavior.

Producer provenance must change at G5. Public paths and semantics must not.
Any incompatible schema or semantic change requires a separate versioned
decision and release after succession.

The compatibility window starts at the G5 receipt. It ends only after:

1. every registered active consumer is green on SDK-produced artifacts;
2. direct predecessor checkout dependencies reach consumer-zero;
3. clean install, upgrade, downgrade, and rollback rehearsals pass;
4. two consecutive SDK main or release validation cycles pass without
   predecessor generation;
5. runtime mirror and artifact-trust records identify the SDK source ref;
6. no unresolved high-severity compatibility regression remains.

R1 does not invent a calendar duration. A release owner may add a calendar
floor before G5, but cannot weaken the evidence-based exit conditions.

## Repository Succession

- Migrate the producer function, contracts, and necessary validation—not the
  predecessor tree as a shape.
- Keep `aoa-routing` canonical through R3 and M1.
- Permit the SDK implementation to run only as a non-publishing shadow until
  G4.
- Switch canonical ownership only through the G5 receipt.
- After G5, land routing features only in the SDK.
- Limit predecessor changes to compatibility, security, rollback, and
  deprecation work.
- Preserve Git history, releases, decisions, and public provenance.
- Retire rollback only after the window and consumer-zero.
- Treat archive readiness as evidence. Treat archive execution as a separate
  irreversible action requiring exact operator approval.

## Control-Plane Boundary

The SDK may own route resolution, explanation, plan compilation, lifecycle
contracts, runtime adapter protocol, and correlation. It may not:

- author agent, skill, capability, scenario, eval, memo, KAG, stats, or
  runtime meaning;
- activate capabilities without the named approval and runtime owners;
- execute models or tools in the control-plane core;
- turn runtime outcome into an eval verdict;
- turn evidence references into canonical durable memory;
- hide a second producer behind a compatibility wrapper.

`AoARunner` is a client of runtime adapters. The first production adapter must
bind to a live runtime-owned contract, preferably the existing governed
`abyss-stack` runner if R2/C4 archaeology confirms that surface.

## Explicit Non-Goals

- no absorption of sibling organs;
- no second `abyss-stack`;
- no universal hidden orchestrator;
- no ABI break inside owner succession;
- no wholesale copy of routing mechanics or KAG shards;
- no cost claim based only on repository count or package size;
- no archive before consumer-zero and explicit approval.

## G1 Verdict

G1 passes for target-model work because:

- the accepted target and live authority are distinct;
- each lifecycle operation has one named authority owner;
- source, runtime, proof, and memory owners remain outside SDK authority;
- owner change and ABI change are separated;
- both repository decisions are required before G5;
- archive remains operator-gated.

G1 does not authorize code migration. R2 must next prove the typed contracts,
lifecycle transitions, golden scenarios, and threat controls before R3.
