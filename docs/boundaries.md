# aoa-sdk Boundaries

`aoa-sdk` exists to consume source-owned generated surfaces and provide typed
Python access to them. It should stay narrow enough that neighboring
repositories remain authoritative.

## Source Ownership

- `aoa-sdk` owns the canonical routing producer and dispatch ABI after the
  receipt-bound G5 switch in `AOA-SDK-D-0076`; this advances, rather than
  erases, the accepted-target/predecessor posture established by
  `AOA-SDK-D-0071`.
- Archived `aoa-routing` preserves the exact predecessor implementation,
  historical ABI, releases, decisions, and deprecation evidence. X1 closed
  compatibility and operational rollback; X2 binds the later separate
  operator approval and public archive without transferring runtime or
  historical source authority into the SDK.
- `aoa-skills` owns shared skill sources, capability families, install
  profiles, port grammar, and portable exports.
- Each repository owns authored procedures and admission for its own skill
  home. `aoa-sdk` owns only procedures over SDK-owned helper contracts.
- The host owns skill discovery and execution; KAG and the executing agent own
  semantic retrieval and task-local composition.
- `aoa-agents` owns role contracts, phase seams, and handoff doctrine.
- `aoa-models` owns model identities, exact realizations, scoped claims,
  studies, and informational fit projections.
- `aoa-playbooks` owns scenario composition surfaces.
- `aoa-memo` owns recall and memory objects.
- `aoa-evals` owns proof surfaces and verdict meaning.
- `Dionysus` owns seed lineage, not runtime authority for the SDK.
- `Agents-of-Abyss` owns constitutional organ-access admission law.
- `abyss-stack` owns MCP package deployment, process and endpoint observations,
  runtime lifecycle, and rollback execution.
- Each organ owner owns its capability and owner-specific payload contract.

## aoa-sdk Should Own

- the canonical routing producer, routing ABI, deterministic route
  resolution, structured explanation, runtime-neutral plan compilation, and
  lifecycle client contracts
- the C1 receipt-bound route resolver, which intersects the canonical routing
  registry with a pinned `aoa-skills` owner projection and blocks ambiguity
  without activation
- the C2 deterministic plan compiler, which consumes an exact admitted
  `aoa-playbooks` contour/schema pin, preserves reviewed input and condition
  provenance, and emits a runtime-neutral `RunPlan` without adapter selection
  or execution
- the post-compile `AgentIncarnationBindingV2`, which validates exact
  owner-qualified task, role, model-realization, runtime/tool, workspace,
  permission, continuation, and wake refs against one immutable `RunPlan`
  without selecting a model or interpreting model fit
- the C3 `AoARunner` lifecycle client, which binds a caller-supplied adapter,
  validates exact runtime observations, approvals, bounded retries, receipts,
  event continuity, outcomes, restore, and closeout without executing a step
- the C4 `abyss-stack` runtime adapter client, which loads an explicitly
  delivered owner profile and constraints, validates exact delivery
  coordinates, and transports lifecycle calls without owning the external
  bridge, runtime policy, effects, or execution evidence
- the C5 evidence-chain composer and repository, which validate exact
  cross-owner identity and completeness across immutable partial revisions
  while keeping eval verdicts, memo contents, checkpoint receipts, and
  closeout payloads in their owner repositories
- the deterministic SDK-owned reference adapter as a no-effect protocol
  witness, never as production runtime or invocation proof
- the wheel-packaged pre-protocol Agon gate-routing bridge, deterministic
  advisory route hints, and owner-dispatch seam; `Agents-of-Abyss` retains
  Agon law and no emitted candidate activates a protocol or runtime effect
- the versioned R2 route, plan, approval, lifecycle, event,
  evidence-reference, and adapter protocol models used by C1-C5; the models
  and Runner do not activate or implement a production runtime
- the historical packaged routing shadow compiler, strict validator, and
  dual-producer sidecar that proved predecessor parity before the G5 switch
- the historical SDK-identified, non-publishing candidate assembly
  bound to exact clean source refs, artifact subjects, and false authority
  flags for stronger-owner trust and isolated/canary review
- the deterministic public release envelope and exact input/verifier
  lock that establish release trust while normal runtime, canonical ownership,
  and all six switch-authority flags remain denied
- the receipt-bound canonical envelope that proves public-release byte parity,
  names the exact runtime contract, starts the compatibility window, and
  authorizes the producer switch while recording archive authority as false;
  the separate runtime owner has since executed the receipt-bound live cutover
- typed loaders over published surfaces
- local workspace discovery and sibling-repo resolution
- shared Python models for stable consumer use
- SDK source-home posture under `sdk/` for public-interface,
  facade-boundary, runtime-entry, and distribution route shape
- root system-design and agent-surface design posture in `DESIGN.md` and
  `DESIGN.AGENTS.md`
- the canonical `skills/` home and admission decisions for SDK-owned Titan
  helper procedures
- durable rationale for SDK-owned topology, route-law, compatibility, and
  validation choices
- mechanics topology cards that map repeatable SDK operations back to their
  active source surfaces
- session and orchestration helpers that preserve source ownership
- policy-aware guards around approval, mutation, and trust posture
- adapters that can change transport without changing ownership
- the protocol-independent organ-access contract models
- the private organ-registry source contract and deterministic projection
  compiler; the configured OS workspace owns the concrete private source
  instance
- owner-bounded catalog, organ and capability inspection, compatibility
  comparison, and activation-plan compilation
- attachment of stack observations and eval evidence as cited inputs without
  promoting them to SDK-authored truth
- deterministic validation of a host-visible, one-stage-at-a-time KAG,
  memo-candidate, eval, and explicit owner-acceptance receipt chain without
  owner invocation
- deterministic collection and replay of owner-issued organ-admission
  evidence, plus non-mutating registry transition preview and separate
  owner/operator decision validation
- exact composition and lookup of owner-qualified evidence refs without
  copying, reinterpreting, or superseding their canonical payloads
- passive skill-environment inspection and exact owner-profile user bootstrap
- reviewed-session closeout helpers that call owner-owned publisher scripts and
  refresh derived stats without taking over workflow or proof meaning

## aoa-sdk Should Not Absorb

- activation or model/tool execution from the runtime owner
- model identity, realization, fit-claim, study, or model-selection meaning
  from `aoa-models`, the caller, or `aoa-evals`
- live runtime execution from the canonical receipt, release archive,
  attestation, trust record, copied runtime mirror, or schema-valid canary
  without the runtime owner's separate cutover receipt
- agent, skill, capability, scenario, eval, memo, KAG, stats, or runtime
  source meaning during routing succession
- authored markdown as the primary runtime API
- copied catalogs from sibling repositories
- decision notes that pretend to be active source truth
- design notes that pretend to replace active SDK source, validators, or
  sibling-owner truth
- mechanics packages that pretend source payload moved or that SDK owns sibling
  meaning
- `sdk/` folders that pretend to be a second Python implementation tree or a
  sibling-source owner
- hidden ranking, routing, or memory policy
- Agon law, live arena state, verdict, scar, rank, retention, or ToS authority
  inferred from an SDK gate candidate
- skill selection, activation, task-local composition, or admission for
  another repository's home
- daemon or service responsibilities
- MCP package deployment, process observation, endpoint lifecycle, credential
  provisioning, or effect execution
- a semantic mega-gateway that proxies owner tools or hides direct owner
  connections
- admission inferred from repository, package, process, endpoint, consumer
  registration, or successful-call presence
- automatic activation from discovery or an activation plan
- registry mutation, proof computation, owner acceptance, or effect activation
  from an admission run, candidate, or SDK authorization receipt
- owner-specific capability semantics flattened into one universal payload
- proof, memory, source, runtime, or external-effect acceptance
- hidden MCP server chaining, owner-tool invocation, proof computation,
  durable memory write, or inferred acceptance inside cross-organ
  orchestration
- project-specific overlays inside portable-core modules

## Practical Rule

Before adding an API, ask three questions:

1. Is it reading or wrapping a source-owned published surface?
2. Does the owning repository remain the place where meaning changes?
3. Can the same API stay valid if transport later changes from local files to
   export bundles or MCP?

If the answer is no, the change likely belongs in a sibling repository instead
of `aoa-sdk`.
