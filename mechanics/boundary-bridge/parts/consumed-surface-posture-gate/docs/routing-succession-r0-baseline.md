# Routing Succession R0 Baseline

Status: G0 passed at `2026-07-23T20:04:51Z`.

Machine-readable evidence:
[`../evidence/routing-succession-r0-baseline.json`](../evidence/routing-succession-r0-baseline.json).

## Claim

This report establishes the live predecessor baseline needed to evaluate a
possible succession of the `aoa-routing` producer into `aoa-sdk`.

It does **not** switch authority:

- `aoa-routing@cde31e568e49c5a50afbd89071cf72abd9733d99` remains the
  canonical source owner and producer.
- `aoa-sdk@cdd3af4e1a7d0f0ffc514b65d6dee3b5b838a530` remains a typed
  consumer.
- `abyss-stack` remains the runtime owner.
- source organs retain their authored semantics.
- `abyss-machine` remains the stronger artifact-trust owner.

The baseline was built from fetched `origin/main` refs, live hosting state,
the running `route-api` container, its mounted mirror, and the host trust
registry. Existing user branches and dirty canonical checkouts were observed
but not normalized or changed.

## R0 Verdict

G0 passes because:

1. all 25 active repositories in the `8Dionysus` organization were covered;
2. every active checkout, runtime, trust, CI, reference, and projection
   consumer found by the scan is classified;
3. all 14 root routing outputs and every other generated or
   generated-named routing surface have an identified producer class;
4. the production load and refresh path was reproduced;
5. every active predecessor surface family has an `absorb`, `merge`,
   `preserve`, `retire`, `archive`, or `external` disposition;
6. the cost hypothesis now has numerical baselines;
7. there are no unclassified dependencies.

This does not mean the current system is healthy. Three pre-existing
conditions are critical:

- the running service is false-green over a stale mirror;
- the mirror cannot currently be refreshed by its declared sync contract;
- the exact current source ref is not admitted by the stronger artifact
  gate.

Those are migration prerequisites and proof requirements, not reasons to
pretend the dependency atlas is incomplete.

## Pinned Primary Baseline

| Surface | `origin/main` | Canonical checkout | Posture | Latest release |
| --- | --- | --- | --- | --- |
| `aoa-routing` | `cde31e568e49c5a50afbd89071cf72abd9733d99` | `72f91d2a8e21438157a853becd136be30e72234e` | clean, behind 2 | `v0.3.0`, 2026-07-14 |
| `aoa-sdk` | `cdd3af4e1a7d0f0ffc514b65d6dee3b5b838a530` | `67d7f7cf9d7f05eed8b8e52a7c5e8ba6d9352c91` | clean, behind 2 | `v0.5.1`, 2026-07-14 |
| `abyss-stack` source | `38856c1e4da1e6e0e40d2b76d8aaf828a7ef4b10` | `ca2078b213a471b994a21b13dfd8f70f8f84cd7c` | user work present; untouched | `v0.4.0` |
| `abyss-machine` | `2faa6c6ccfc1309f6c3b6a36ddf04c3334c4547b` | active user branch | user work present; untouched | host trust owner |

Both `aoa-routing` and `aoa-sdk` protect `main` with strict `Repo
Validation` and enforced admin checks. Neither current GitHub release carries
release assets. The SDK tag workflow builds an Actions artifact; routing has
no equivalent package build.

The full repository/SHA/dirty ledger is in the evidence file. It is included
to prevent a later worktree from silently treating a stale or dirty sibling
as canonical input.

## Producer Graph

The live state corrects one assumption in the program metric:

| Metric | Live baseline |
| --- | --- |
| canonical routing owners | 1 (`aoa-routing`) |
| runnable routing producer implementations | 1 |
| active repository control planes involved | 2 |
| direct producer input repositories | 14 |
| canonical root outputs | 14 |

Therefore succession must measure:

```text
canonical owners:          1 -> 1
runnable implementations:  1 -> 2 (shadow) -> 1
active repo control planes: 2 -> 1
```

Claiming `canonical producers: 2 -> 1` would be false at R0. The future
shadow implementation is not canonical merely because it can run.

`scripts/build_router.py`, `scripts/router_core.py`, and
`scripts/validate_router.py` currently read:

```text
aoa-techniques
aoa-skills
aoa-evals
aoa-memo
aoa-stats
aoa-agents
Agents-of-Abyss
aoa-playbooks
aoa-kag
Tree-of-Sophia
aoa-sdk
Dionysus
8Dionysus
abyss-stack
```

The release lane adds `abyss-machine` as a fifteenth sibling checkout.
Release-quality evidence therefore depends on explicit pinned roots; default
filesystem discovery is not sufficient.

### Root Output Family

All names below are compatibility surfaces and must remain stable during the
owner-only switch:

```text
generated/aoa_router.min.json
generated/cross_repo_registry.min.json
generated/task_to_surface_hints.json
generated/task_to_tier_hints.json
generated/quest_dispatch_hints.min.json
generated/federation_entrypoints.min.json
generated/return_navigation_hints.min.json
generated/recommended_paths.min.json
generated/kag_source_lift_relation_hints.min.json
generated/composite_stress_route_hints.min.json
generated/stats_regrounding_hints.min.json
generated/owner_layer_shortlist.min.json
generated/pairing_hints.min.json
generated/tiny_model_entrypoints.json
```

The current bundle has 34 subjects: these 14 outputs, 15 schema surfaces,
three producer/validator files, the authority README, and the generated route
card.

Other generated families are classified separately:

- the Agon gate registry has its own part-local builder;
- decision indexes have the decision-index generator;
- 396 KAG shard files belong to the `aoa-kag` indexing contour;
- the quest-board and RPG files named `generated/*.example.json` are authored
  examples, not live producer outputs;
- the local stats packet is an authored reference packet.

No generated file remains with an unknown producer class.

## Consumer Atlas

### Hard and runtime consumers

| Consumer | Dependency |
| --- | --- |
| `aoa-sdk` | two workflows, workspace roots, six compatibility surfaces, routing readers, A2A return refs, recurrence projections |
| `abyss-stack` | runtime mirror, ten route-api inputs, sync/layout validators, governed target policies and fixtures |
| `aoa-evals` | latest-sibling workflow, `AOA_ROUTING_ROOT`, canary matrix and runtime-integrity evidence |
| `aoa-kag` | two workflows, pinned provider record, `.deps/aoa-routing`, generation context |
| `aoa-agents` | optional routing root and task/tier/tiny-entry validators |
| `aoa-stats` | absolute fallback path plus recommended-path/owner-shortlist downstream canaries |
| `abyss-machine` | artifact class policy, verifier fixtures, bundle registry and subject store |

### Constitutional, public, and reference consumers

- `Agents-of-Abyss` names routing as a distinct organ and publishes derived
  role maps.
- `8Dionysus` names the public route and its required check contract.
- `Tree-of-Sophia` validates a tiny-entry route reference.
- `aoa-techniques`, `aoa-memo`, and `aoa-playbooks` contain current reference
  surfaces mixed with historical evidence.
- `Dionysus` is both a producer input and a historical/public route source.
- `aoa-session-memory` has one naming golden-set fixture.
- `ATM10-Agent` has derivative skill guidance only.

The six connectors and `aoa-editing` have no `aoa-routing` reference at their
fetched `origin/main`.

An archived `abyss-stack_old` repository was explicitly excluded from the
active consumer set.

## Live Runtime Loading Map

The actual production path is:

```text
/srv/AbyssOS/aoa-routing
  -> aoa-sync-federation-surfaces
  -> /srv/AbyssOS/abyss-stack/Knowledge/federation/aoa-routing
  -> read-only bind mount /app/federation/aoa-routing
  -> route-api
```

The running container is
`14ee45d6ec486bc81e2ca0b32225dd5c29ba878468e22771497ae143bcec6981`,
using `localhost/abyss_route-api:latest` and listening on
`127.0.0.1:5402`.

The source and runtime artifacts are not aligned:

| Artifact | SHA-256 | Entries | Identity |
| --- | --- | ---: | --- |
| routing `origin/main` | `098c6c781227d7d670780196dda5dbce5a21569a05db3a4492738e84f6c8275b` | 168 | `aoa_routing_thin_router_v1` |
| stale canonical checkout | `438ed1690df4fb02e866b02f0d9561fc2b7b28c13a49ac14fdfad626b08fde85` | 217 | `aoa_routing_thin_router_v1` |
| live runtime mirror | `72bf60dc5cd2fe190e00e91c1e948fcf0c1a08f5884d51d23b120946c969e2c1` | 123 | absent |

The runtime blob matches routing commit
`4d2b29d01588ed5e033afcf40ec41fc26a334a5b` from 2026-03-28. It was 116.2
days old at capture.

Across the 14 current root outputs:

- 2 match the mirror;
- 8 are stale;
- 4 are absent.

The sync contract requires 23 legacy-shaped files but fails first on
`docs/FEDERATION_ENTRY_ABI.md`. The current routing owner moved that authority
to
`mechanics/boundary-bridge/parts/federation-entry/docs/federation-entry-abi.md`;
the runtime mapper was never updated. The recurrence doc and schema family
have the same former-flat-path problem.

`/health` still says ready because it checks presence and selected version
fields, not:

- artifact identity;
- source commit;
- content digest;
- mirror manifest;
- trust admission.

The service also has no free-text `RouteIntent`. A reproduced
`bounded-plan-shaping` request returns advisory tier, role, and artifact
references. It does not return a `RunPlan`.

## Trust Baseline

The stronger host registry contains a release-ready record:

```text
record:
  sha256:3cf0ea3b1db4e03a2e532feecbf6cddca78c92936b4718307587c169c2625a48
artifact class:
  thin_routing_readmodel_bundle
ABI digest:
  sha256:438ed1690df4fb02e866b02f0d9561fc2b7b28c13a49ac14fdfad626b08fde85
subject-family digest:
  sha256:c1963f697ce28b090187574e48346c6359c689b14060da458ba49a826e7af348
controls:
  abi_signature, sbom, slsa_in_toto
```

That record is valid for its recorded filesystem source, not for current
`origin/main`. Exact admission against
`cde31e568e49c5a50afbd89071cf72abd9733d99` returns `deny` with
`source_ref_mismatch`.

No later owner switch may cite this predecessor record as proof for an SDK
source ref. A new exact-ref admission is mandatory.

## Surface Disposition

| Predecessor surface | Disposition | Target posture |
| --- | --- | --- |
| builder and router core | `absorb` | SDK-local compiler implementation |
| validator and producer/ABI tests | `merge` | SDK routing validation |
| 14 output filenames and ABI epoch | `preserve` | SDK-produced compatibility projection |
| core schemas and schema IDs | `absorb`, `preserve` | package data plus legacy identifiers |
| thin-router bundle manifest | `merge` | SDK declaration with versioned owner metadata |
| seven producer-coupled mechanic schema parts | `merge` | nearest SDK mechanic/package home |
| Agon gate routing registry | `merge` | SDK routing/Agon bridge below constitutional semantics |
| duplicate recurrence/via-negativa scaffolding | `retire` | existing SDK mechanic owners |
| remaining non-ABI routing mechanic prototypes | `archive` | predecessor history; no default copy |
| 25 installed `.agents/skills` bundles | `external`, `retire` | skill owner/install surface |
| 396 KAG shard files | `retire`, regenerate | fresh SDK index |
| old decisions/indexes | `preserve`, `archive` | predecessor rationale plus paired succession decisions |
| root docs, source-home, release route | `merge`, `archive` | distilled successor routes and predecessor history |
| quests, eval reports, Spark, legacy | `archive` | history; re-author only live obligations |
| local stats port | `merge` | SDK stats question and fresh packet |
| routing workflows/release contour | `retire` after window | SDK contour; shadow parity is temporary |
| broad copied sibling fixtures | `retire` | minimal pinned compatibility corpus |
| repository | `archive` only after consumer-zero | irreversible gate remains operator-owned |

This disposition intentionally does not copy the old tree. R2 may derive a
new typed contract from historical prototypes, but history does not become
active SDK source merely because a similarly named feature is needed.

## Cost Baseline

### CI

The five measured validation/recurring workflows account for 430 completed
runs and 476.97 runner-minutes in the sampled windows:

| Workflow | Sample | Success | Failure | Runner minutes | Median |
| --- | ---: | ---: | ---: | ---: | ---: |
| SDK Repo Validation | 100 | 88 | 12 | 118.83 | 70 s successful |
| Routing Repo Validation | 100 | 88 | 12 | 157.85 | 101 s successful |
| Routing Compatibility Canary | 100 | 29 | 71 | 95.50 | 48 s all |
| SDK Latest Sibling Canary | 30 | 0 | 30 | 19.15 | 36 s all |
| SDK Federation Release Cadence | 100 | 0 | 100 | 85.63 | 50 s all |

The three known failing canary contours consumed 156.73 failed
runner-minutes. The two repo validations have a 101-second successful
parallel critical path and 171 successful runner-seconds when both
repositories change.

Current CI loads:

- 16 repository roots for routing repo validation;
- 15 for routing compatibility canary;
- 10 for SDK latest-sibling canary;
- 14 for SDK release cadence.

### Duplication

The two repositories share:

- 18 top-level surface names;
- 10 mechanics family names;
- 6 root script names;
- 2 release streams;
- separate decision, KAG, stats, quest, release-check, and nested-agent
  control planes.

The runtime adds a manual 23-file copy contour with no host timer or hook
found to keep it current.

### Changed-together history

Since 2026-04-01:

- routing: 154 commits across 44 active days;
- SDK: 293 commits across 55 active days;
- 41 days overlap;
- 147 routing commits occurred on common active days.

Since 2026-06-01, 16 of 18 routing-active days overlap SDK activity. A
temporal-coupling proxy found a mean 10.89 of 14 family repositories touched
on routing author-days. This is coordination pressure, not proof that each
repository was causally required.

Four of five routing releases were paired with SDK releases within seconds.
The fifth belonged to the same 2026-07-14 release wave.

### Agent/process baseline

The old contour cannot natively measure a full intent-to-closeout cycle
because it has no:

- free-text intent resolver;
- `RouteDecision -> RunPlan` compiler;
- `RunPlan -> SessionHandle` runner;
- unified session-to-closeout chain.

This is recorded as `unsupported`, not as zero time or zero cost. The
smallest observed route requires manual task-family classification and
returns only advisory references. Artifact maintenance has a measured lower
bound of 15–16 repository contexts in CI.

E1 must replay identical tasks and count calls, loaded roots, bytes/manual
transformations, elapsed time, and evidence completeness. Unsupported old
stages remain explicit.

## Known Failure Modes

Fourteen modes are baselined:

1. false-green runtime health;
2. stale mirror content;
3. missing mirror provenance manifest;
4. former-flat-path sync failure;
5. exact-ref artifact admission denial;
6. missing producer input-revision matrix;
7. current `aoa-skills` drift breaking routing canary;
8. `aoa-agents` v2 drift breaking SDK canary;
9. stale KAG/route expectations in SDK canary;
10. shallow-clone release audit false-red;
11. default root discovery selecting stale or dirty inputs;
12. hard-coded `aoa-routing` paths and checkout roots;
13. owner-metadata changes threatening byte parity;
14. copying repository scaffolding instead of reducing it.

The evidence JSON binds each risk to a control.

## Compatibility Corpus Required Before Owner Switch

At minimum:

- byte fixtures for all 14 current outputs;
- a rebuild fixture with all 14 input refs pinned;
- the 34-subject bundle declaration;
- legacy schema IDs and `aoa_routing_thin_router_v1`;
- negative stale, missing, malformed, and forbidden-owner cases;
- the SDK six-surface reader corpus;
- agent tier/surface/tiny-entry fixtures;
- stats and KAG downstream fixtures;
- the 23-path runtime mirror and its manifest;
- route-api response and health-provenance fixtures;
- exact-source-ref trust admission;
- clean package install with no `aoa-routing` checkout;
- rollback and organization-wide consumer-zero scanners.

## G0 Stop Line

R1 may now define the Target Operating Model and paired durable decisions.

No producer code should move, no canonical output should switch owner, and no
runtime source should be redirected until:

1. G1 has one unambiguous owner per operation;
2. G2 proves common typed contracts for the three golden scenarios;
3. the owner-only ABI policy separates preserved identifiers from changed
   provenance;
4. the false-green runtime and exact-ref trust requirements are incorporated
   into the migration gates.
