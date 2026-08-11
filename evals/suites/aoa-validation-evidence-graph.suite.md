---
schema_version: local_eval_suite_note_v1
owner_repo: aoa-sdk
status: draft
authority_boundary: owner-local evidence support only; no verdict, scoring, regression, or proof doctrine authority
---

# Validation evidence graph comparative suite

## Invariant

For an exact owner source state and requested claim set, the planner must
activate every evidence producer required by those claims, include every
dependency, execute only explicit argv without a shell, retain exact identity
and outcomes in one receipt, and fail closed on unknown routes, missing
evidence, collisions, cycles, timeouts, failures, stale identity, or tampering.

Optimization may change scheduling, process boundaries, and safe reuse. It may
not delete a claim, substitute a weaker check, turn a skip into success, infer
sufficiency from a green proxy, or let a partial shadow route authorize the
owner gate.

## Compared methods

The fixed oracle is the unchanged serial `scripts/release_check.py` battery
plus explicit workflow prerequisites. Every candidate is compared against the
same source commit, interpreter/dependency identity, claim set, and effective
test/evidence corpus:

1. serial execution;
2. ordinary pytest and the complete isolated G11 wrapper as two DAG nodes;
3. `pytest-xdist` with two and four workers using file-level scheduling;
4. `pytest-xdist` with test-level scheduling, including its nested-process cost;
5. static duration-balanced pytest and G11 shards;
6. the owner-local dependency-aware claim/evidence graph;
7. path-to-claim routing in non-authoritative shadow mode;
8. exact-identity receipt reuse, once a reuse contract exists.

No candidate is rejected from a single noisy measurement. Local trials use
interleaved cold and warm pairs. Hosted trials normally use at least three
paired PR runs. A latency candidate is accepted only when the improvement is
reproducible in at least two of three hosted pairs and is material: at least 15
percent or 60 seconds on the relevant critical path. A resource-only candidate
may be retained separately when it has a clear bounded benefit.

## Cases

### Positive

- the full profile activates all declared claims, all required evidence, and
  all dependencies;
- every non-pytest command from the serial release battery occurs exactly once;
- the ordinary pytest node excludes only the G11 wrapper, while two static G11
  shards cover every declared exact wrapper case once;
- independent nodes overlap and canonical fan-in remains in manifest order;
- a full successful receipt binds source, manifest, commands, environment,
  evidence, timings, and a sufficient full-owner decision;
- the instant profile validates graph identity and topology within its one
  second owner-local process budget.

### Negative

- an unknown changed path falls back to the full claim set;
- a requested claim without a provider blocks before execution;
- a failed or timed-out required node produces missing evidence and an
  insufficient decision;
- an upstream failure blocks dependants and prevents new costly work from
  starting;
- changed paths without explicit shadow mode are rejected;
- a partial shadow result remains non-authoritative even when all selected
  nodes pass.

### Collision and tamper

- duplicate claim, route, node, step, or evidence-provider identity is invalid;
- a dependency cycle is invalid;
- unsafe absolute/traversing paths and NUL-bearing argv are invalid;
- a receipt or reuse candidate with a changed manifest, command, input,
  environment, repository state, or evidence digest is rejected rather than
  partially trusted;
- two evidence producers may not silently claim the same evidence identity.

### Regression and no-miss

- the serial command inventory remains the completeness oracle until owner
  review explicitly supersedes it;
- seeded edits across source, tests, schemas, generated companions, workflow,
  package, docs, eval, and unknown paths compare shadow selection with the full
  oracle;
- every seeded failure detected by the full oracle must be detected by the
  activated candidate graph; the accepted false-green count is zero;
- G11 preserves per-case child pytest isolation, exact node IDs, timeouts, and
  failure stdout/stderr even when wrapper cases are statically sharded;
- warm-cache and repeated identical-run experiments are reported separately
  from cold correctness evidence.

## Runner input and output

Input is an exact repository state, the reviewed graph manifest, one named
profile or explicit shadow changed-path set, a bounded worker count, and the
current interpreter/dependency environment. Execution uses direct argv from
the repository root and inherits only the invoking environment; it does not
invoke a shell.

Output is one canonical `aoa_validation_evidence_receipt_v1` containing the
repository, manifest, environment, requested claims, activated nodes, ordered
node/step results, command and output digests, bounded output tails, timings,
required/satisfied/missing evidence, routing posture, and sufficiency decision.
The receipt is written atomically when a path is requested.

Accepted mechanical outcome requires exit `0`, every activated node passed,
no required evidence missing, and a full-profile non-shadow receipt before the
owner gate may treat it as full validation. Shadow results can compare routes
but cannot authorize landing.

## Initial measured observations

The first local exploration on Python 3.14 established a provisional baseline,
not a verdict:

| candidate | pytest wall | CPU | peak memory | observation |
|---|---:|---:|---:|---|
| full serial pytest | 75.52 s | 76.79 s | 429 MB | 799 passed, 2 skipped, 537 subtests |
| ordinary only | 37.21 s | 38.74 s | 363 MB | G11 wrapper excluded, remaining corpus intact |
| complete G11 wrapper | 42.87 s | 41.16 s | 170 MB | 16 isolated cases |
| ordinary + complete G11 DAG | 47.79 s | 89.23 s | 533 MB | all evidence, 36.7% less wall than serial |
| xdist 2, loadfile | 53.63 s | 94.82 s | 677 MB | slower than bounded DAG |
| xdist 4, loadfile | 43.63 s | 93.19 s | 935 MB | faster, materially heavier |
| xdist 4, test-level load | 59.03 s | 121.35 s | 879 MB | nested child-process amplification |
| ordinary + two static G11 shards | 39.45 s | 79.14 s | 526 MB | 47.8% less wall with near-baseline CPU |
| paired full serial release battery | 130.28 s | 117.63 s | 381 MB | unchanged `scripts/release_check.py` oracle |
| full evidence graph, 4 workers | 46.73 s | 148.86 s | 794 MB | 64.1% less wall; excess CPU and memory |
| full evidence graph, 3 workers | 48.25 s | 114.10 s | 688 MB | 63.0% less wall; lower CPU than serial |

The instant profile additionally completed ten consecutive owner-local process
runs with 0.2733 s minimum, 0.3105 s median, 0.3171 s p90, and 0.3185 s
maximum, using 34.4 MB peak memory for the enclosing measurement unit.

These runs occurred under live host conditions and need interleaved repetition
plus hosted CI pairs. They justify the static-DAG pilot; they do not yet select
an OS-wide default.

## Cleanup and effects

The suite creates only normal test/build temporaries and an explicitly named
receipt. Benchmark-only environments and JUnit/timing artifacts live in the
host-managed `/srv/abyss-machine/tmp/ai` lane. Failed child process groups are
terminated on timeout. No sibling source, live service, owner policy, or
published artifact is mutated.

## False-green guards and proof ceiling

Strict manifest keys, unique identities, cycle detection, unique evidence
providers, full fallback for unknown paths, direct argv, exact G11 case union,
serial-command inventory regression, receipt digests, and shadow-only routing
are mandatory guards. Hosted green status alone is not enough: receipts and
the paired oracle comparison must agree.

This local design can support a bounded scheduling and sufficiency claim for
the pinned `aoa-sdk` gate. It does not prove central eval acceptance, safe
partial routing, safe cross-run reuse, sibling-owner adoption, AbyssOS-wide
benefit, production runtime health, or real-session time-to-merge reduction.
Those claims require owner review, central routing, per-repository adoption,
post-merge proof, and fresh session evidence.
