---
schema_version: local_eval_report_note_v1
owner_repo: aoa-sdk
status: reviewed
authority_boundary: owner-local scheduling admission only; no central verdict, scoring, regression, or proof doctrine authority
---

# Validation evidence graph hosted comparison report

## Bounded question

Can the `aoa-sdk` full validation battery use a bounded dependency-aware graph
instead of serial execution while preserving every required evidence unit,
failing closed on identity defects, and reproducibly reducing the hosted
critical path?

This report answers only for the pinned SDK owner gate. It does not issue an
`aoa-evals` verdict and does not authorize path-based partial validation,
cross-run receipt reuse, or sibling-owner rollout.

## Evidence identity

- PR head: `1976a8a93937c0882a2f7f3d064f278acf561534`
- hosted PR merge commit: `b07516070f5851c7b05159927368ec563eae4681`
- hosted PR merge tree: `e72b057af85718d7310352287df7426cfde031f7`
- Python: CPython 3.12.13 on `ubuntu24`
- installed-package versions: 0.10.2 (aoa-sdk), 9.1.1 (pytest), 2.3.0
  (mypy), 0.16.2 (Ruff), and 1.5.0 (PyPA build library)
- serial workflow: GitHub Actions run `31528506217`, attempts 1 through 3
- graph workflow: GitHub Actions run `31528506139`, attempts 1 through 3
- graph artifacts: `validation-evidence-shadow-31528506139-1`, `-2`, and
  `-3`

Both workflows used the same eight checkout, KAG, history, verifier, Python,
dependency, and G4 prerequisite steps before their compared command. GitHub
checked out the same synthetic merge commit and tree in all three receipts.

## Hosted paired outcome

| attempt | serial core | graph receipt | core reduction | serial job | graph job | graph evidence |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 96 s | 57.545 s | 40.1% | 174 s | 115 s | 14/14, sufficient |
| 2 | 135 s | 65.899 s | 51.2% | 193 s | 130 s | 14/14, sufficient |
| 3 | 137 s | 67.373 s | 50.8% | 197 s | 131 s | 14/14, sufficient |

Median compared-core duration changed from 135 to 65.899 seconds, a 51.2
percent reduction. Median whole-job duration changed from 193 to 130 seconds,
a 32.6 percent reduction. Every pair exceeded the predeclared 15 percent
materiality threshold; two pairs additionally saved more than 60 seconds on
the compared core.

All three graph receipts reported:

- every one of the 14 activated nodes passed;
- every one of the 14 required evidence IDs was satisfied;
- no missing or unreadable input and no integrity blocker;
- stable repository and graph-manifest identity through execution;
- two pinned nested verifier repositories bound wherever full-tree inputs were
  declared;
- full-profile, non-shadow, owner-gate-authoritative scope.

Graph CPU time across the three `/usr/bin/time -v` envelopes was approximately
160.1, 188.5, and 195.8 seconds. Largest-process maximum RSS was approximately
329 MB in each run; this is not aggregate process-tree memory. Hosted serial
resource envelopes were not collected, so the local cgroup comparison remains
the resource-balance evidence rather than an invented hosted comparison.

## Negative witness before acceptance

The first pre-fix pair on `dbe105b3` was rejected. Python 3.12 exposed a
version-sensitive recursive glob in a new identity test, and nested
`.aoa-stats-validator` and `.abyss-machine-verifier` checkouts appeared as
directory entries that the graph conservatively classified as unreadable.
The serial run failed the same test; the graph additionally emitted an
insufficient receipt with `node_inputs_unreadable` instead of reporting a
false green.

The follow-up bound recursive patterns independently of Python glob behavior,
represented nested Git checkouts by their commit, tree, status, patch, and
untracked identities, and made absent owner Git identity an explicit
`repository_identity_unavailable` blocker. The corrected contract completed
18/18 focused tests locally before the three accepted hosted pairs.

## Method selection

The local comparison retained serial, two-node DAG, `xdist` two/four-worker
file scheduling, `xdist` test scheduling, static shards, and three/four-worker
full graphs. Test-level `xdist` amplified nested G11 processes; four-worker
variants increased peak memory materially. The selected three-worker graph
combined the exact static G11 partition with dependency-aware build fan-out
and gave the best measured latency/resource balance without deleting a claim.

## Owner admission and rollback

The predeclared rule required at least two of three same-commit hosted pairs,
zero evidence miss or false green, and at least 15 percent or 60 seconds of
critical-path improvement. All three corrected pairs passed that rule.

The owner-local result supports making the full graph the default SDK release
gate. The ordered serial `COMMANDS` inventory remains executable through the
documented serial mode of `scripts/release_check.py` and through the manual
serial-oracle workflow. Changed-path routing remains `shadow_only`; cross-run
reuse remains absent.

## Proof ceiling

This evidence supports one owner-local scheduling and sufficiency decision for
the pinned full `aoa-sdk` gate. It does not prove central eval adoption,
AbyssOS-wide savings, safe partial routing, safe receipt reuse, post-merge
stability, or real-session time-to-merge improvement. Those require owner-local
rollouts, final main-branch proof, and fresh session observation.
