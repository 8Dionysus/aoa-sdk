# aoa-sdk Boundaries

`aoa-sdk` exists to consume source-owned generated surfaces and provide typed
Python access to them. It should stay narrow enough that neighboring
repositories remain authoritative.

## Source Ownership

- `aoa-routing` currently owns navigation surfaces, the canonical routing
  producer, and the dispatch ABI.
- `AOA-SDK-D-0071` accepts transfer of that producer and ABI to `aoa-sdk`,
  but the transfer is not live until shadow parity and the explicit G5
  owner-switch receipt. Before G5, SDK routing output is consumer or
  non-publishing shadow evidence only.
- `aoa-skills` owns shared skill sources, capability families, install
  profiles, port grammar, and portable exports.
- Each repository owns authored procedures and admission for its own skill
  home. `aoa-sdk` owns only procedures over SDK-owned helper contracts.
- The host owns skill discovery and execution; KAG and the executing agent own
  semantic retrieval and task-local composition.
- `aoa-agents` owns role contracts, phase seams, and handoff doctrine.
- `aoa-playbooks` owns scenario composition surfaces.
- `aoa-memo` owns recall and memory objects.
- `aoa-evals` owns proof surfaces and verdict meaning.
- `Dionysus` owns seed lineage, not runtime authority for the SDK.

## aoa-sdk Should Own

- after G5, the canonical routing producer, routing ABI, deterministic route
  resolution, structured explanation, runtime-neutral plan compilation, and
  lifecycle client contracts
- before G5, the versioned R2 route, plan, approval, lifecycle, event,
  evidence-reference, and adapter protocol models used to prove the boundary;
  the models do not activate an `AoASDK` runner or runtime
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
- passive skill-environment inspection and exact owner-profile user bootstrap
- reviewed-session closeout helpers that call owner-owned publisher scripts and
  refresh derived stats without taking over workflow or proof meaning

## aoa-sdk Should Not Absorb

- activation or model/tool execution from the runtime owner
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
- skill selection, activation, task-local composition, or admission for
  another repository's home
- daemon or service responsibilities
- project-specific overlays inside portable-core modules

## Practical Rule

Before adding an API, ask three questions:

1. Is it reading or wrapping a source-owned published surface?
2. Does the owning repository remain the place where meaning changes?
3. Can the same API stay valid if transport later changes from local files to
   export bundles or MCP?

If the answer is no, the change likely belongs in a sibling repository instead
of `aoa-sdk`.
