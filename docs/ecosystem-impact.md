# Ecosystem Impact Of Introducing `aoa-sdk`

## Immediate Change

`aoa-sdk` adds a canonical Python consumer layer to the AoA federation. Before
this repository exists, typed loading and orchestration glue risk being
reimplemented inside each downstream tool. With this repository in place, the
federation gains one explicit software spine for consuming source-owned
generated surfaces without moving ownership away from the source repositories.

## What It Unlocks

- One import path for downstream consumers such as ATM10-Agent, local scripts,
  notebooks, CI helpers, and future MCP or A2A bridges.
- Reusable typed models over routing, skills, agent-phase seams, memo, and eval
  surfaces instead of ad hoc JSON parsing in each consumer.
- A local-first orchestration seam that can close part of the current gap
  between contract-rich repositories and selective runtime adoption.
- A clearer place to express transport adapters, policy gates, session helpers,
  and artifact envelopes without pushing those concerns into `Dionysus` or the
  source canons.

## What It Changes For Neighbor Repositories

- `Dionysus` can stay the seed garden; it no longer needs to carry the SDK as a
  growing runtime seed inside a coordination repository.
- `aoa-routing` can remain the thin navigation layer while `aoa-sdk` becomes a
  consumer of routing surfaces rather than a rival router.
- `aoa-skills`, `aoa-agents`, `aoa-playbooks`, `aoa-memo`, and `aoa-evals` gain
  a typed downstream integration target, which raises the value of their
  generated surfaces and schema stability.
- `abyss-stack` and future clients get a cleaner path to consume federation
  contracts through Python instead of baking direct cross-repo parsing into the
  runtime body.

## New Obligations

- Surface compatibility now matters at package level, not only at repository
  level, so version negotiation and fixture coverage will become necessary.
- The SDK must preserve provenance and source references so convenience APIs do
  not become shadow authority.
- Local-first support should stay truthful: the SDK should not promise live
  runtime capabilities that only exist in source or trial form.
- Release discipline will matter because package consumers will treat the SDK as
  an explicit contract surface.

## Main Risks

- The SDK could drift into a shadow federation center by hard-coding meaning
  that belongs in sibling repositories.
- Convenience APIs could outrun source truth and recreate the same
  source-versus-runtime ambiguity already flagged in the ecosystem audit.
- Project-specific overlays could leak into portable-core modules and weaken the
  reuse story.
- A package that grows too quickly into orchestration breadth could become the
  hidden monolith the federation was designed to avoid.

## Recommended Growth Order

1. Keep the first releases read-oriented and local-first.
2. Add typed loaders and fixtures for published generated surfaces.
3. Add session, artifact, and policy helpers only after the read path is
   stable.
4. Add memo, playbook, and eval bridges after compatibility boundaries are
   explicit.
5. Add remote adapters last, once the local contract is trustworthy.
