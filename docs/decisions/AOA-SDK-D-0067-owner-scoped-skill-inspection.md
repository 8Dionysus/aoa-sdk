# Owner-Scoped Skill Inspection

## Status

Accepted.

This decision supersedes the active skill-runtime behavior recorded by
AOA-SDK-D-0017, AOA-SDK-D-0038, and the `skills/detector.py` stop-line in
AOA-SDK-D-0060. Their historical placement and naming rationale remain part of
the repository record; they no longer justify SDK-owned skill routing,
activation, manual equivalence, or session state.

## Index Metadata

- Decision ID: AOA-SDK-D-0067
- Original date: 2026-07-15
- Surface classes: public API, compatibility, workspace bootstrap, mechanics, owner boundary
- SDK facets: skill environment inspection, typed contracts, workspace bootstrap, boundary bridge
- Mechanic parents: boundary-bridge, runtime-seam, checkpoint
- Guard families: owner scope, no hidden routing, profile parity, compatibility, manual evidence
- Posture: accepted

## Context

`aoa-skills` replaced its project-foundation rings, tiny router, runtime
activation aliases, and skill-session contract with seven curated source
bundles, explicit install profiles, owner-home ports, and a typed capability
graph. Only the reviewed `user-default` profile is admitted for implicit user
installation; repository-owned skills are admitted and projected by their own
repositories.

The existing SDK still read removed owner surfaces, ranked and dispatched
skills, wrote activation sessions, treated router-only results as manual
equivalence, installed a shared workspace skill set, and generated workspace
`AGENTS.md`. Manual trials against the new owner surfaces showed that this path
either fails on missing generated files or selects stale workspace copies. It
also merges user, repository, workspace, and source-export locations into one
ambiguous availability claim.

## Options Considered

- Map the new capability graph back into the old detector, activation, and
  session contracts.
- Remove the SDK skill facade entirely and require every consumer to parse
  owner JSON and filesystem roots directly.
- Keep a passive typed facade that reads exact owner contracts, preserves
  scope, and installs only an explicitly named owner profile.

## Decision

Replace the skill-runtime bridge with an owner-scoped skill-environment
inspector.

The SDK may:

- read the owner skill catalog, resolved install profiles, portable export
  map, MCP dependency manifest, and capability graph through explicit
  compatibility rules;
- look up an exact capability node and its typed relations without ranking,
  retrieval, composition, activation, or task-local DAG construction;
- inspect user, repository, legacy workspace, and source-export roots as
  separate scopes, including duplicate names and structural drift;
- plan or execute an exact copy of an explicitly named user-scoped owner
  install profile into the host-selected user root;
- expose repository-scoped profiles for typed inspection while leaving every
  repository projection to that repository's admitted home-port builder.

The SDK must not:

- select, rank, dispatch, activate, deactivate, or compact skills;
- create SDK-owned skill-session state or represent manual work as skill
  activation;
- install a shared workspace skill layer or write workspace guidance;
- infer a repository home from `.agents/skills` without an admitted
  `skills/port.manifest.json`;
- merge same-name user, repository, legacy workspace, or source-export entries
  into one availability result;
- perform semantic retrieval or task-local DAG composition owned by KAG and
  the executing agent runtime.

The supported CLI contour becomes inspection and exact capability lookup.
Workspace bootstrap consumes an explicit user-scoped owner profile, defaults
to `user-default`, uses copies, and never mutates repository projections,
workspace `AGENTS.md`, or legacy workspace projections.

Checkpoint wrapper and carrier candidate intelligence from AOA-SDK-D-0063
and AOA-SDK-D-0064 remains valid. It may surface review candidates, but it
cannot call the retired detector or turn a candidate into a skill install.

## Rationale

Skill meaning, admission, and projection truth belong to the skill owner.
Execution belongs to the host; deep retrieval and capability composition
belong to KAG and the task-local runtime. The SDK adds value only where typed
compatibility, exact lookup, scope-preserving inspection, and reproducible
profile application would otherwise be reimplemented by every consumer.

Keeping roots separate prevents a stale workspace copy from impersonating a
current user or repository skill. Exact graph lookup exposes typed capability,
workflow, guard, tool, adapter, and skill identities without collapsing them
back into the old assumption that every useful operation is a skill.

## Consequences

- The public `detect`, `dispatch`, `enter`, `guard`, activation, disclosure,
  and skill-session APIs and commands are removed rather than retained as
  compatibility aliases.
- Boundary Bridge owns the new skill-environment-inspector part; the old
  skill-runtime-bridge becomes provenance, not an active part.
- Runtime Seam keeps workspace bootstrap, but its contract changes from
  workspace foundation installation to exact user-profile installation;
  repository profiles route back to their owner builders.
- Surface and checkpoint helpers must use their own typed evidence and
  capability identifiers instead of `SkillDetectionReport` or `SkillSession`.
- Legacy workspace projections are observable but never selected, repaired,
  or deleted implicitly.
- The SDK repository gains no home skill merely for topology symmetry. A
  future `skills/` home requires its own admitted capability evidence.
- This is a breaking public-contract change and belongs to the next minor
  pre-1.0 release line.

## Source Surfaces

- `src/aoa_sdk/contracts/skills.py`
- `src/aoa_sdk/skills/`
- `src/aoa_sdk/cli/skills.py`
- `src/aoa_sdk/workspace/bootstrap.py`
- `src/aoa_sdk/contracts/workspace.py`
- `src/aoa_sdk/compatibility/policy.py`
- `mechanics/boundary-bridge/parts/skill-environment-inspector/`
- `mechanics/runtime-seam/parts/portable-workspace-bootstrap/`
- `docs/boundaries.md`
- `docs/versioning.md`

## Follow-Up Route

Prove the new behavior first with manual current, missing, drifted,
coexistence, legacy-workspace, exact-node, and environment-override trials.
Only then retain regression tests for invariants that those trials establish.
Route semantic retrieval and task-local DAG work to `aoa-kag`; route skill
admission and projection truth to the owning skill repository.

## Verification

- decision index generation and nested-agent validation;
- manual profile bootstrap and environment inspection trials against current
  `aoa-skills` and a repository-owned skill home;
- Boundary Bridge and Runtime Seam part validation after the manual baseline;
- root source-topology, workspace-control-plane, compatibility, package, and
  release gates before landing.
