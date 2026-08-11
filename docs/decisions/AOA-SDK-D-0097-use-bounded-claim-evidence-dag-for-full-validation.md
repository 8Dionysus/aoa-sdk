# Use a bounded claim/evidence DAG for full validation

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0097
- Original date: 2026-08-11
- Surface classes: workflow, validation guard, release control-plane
- SDK facets: validation, release support, control-plane
- Mechanic parents: release-support
- Guard families: claim/evidence sufficiency, serial oracle, identity binding, rollback
- Posture: accepted

## Context

The root release gate accumulated independent source, test, typing, build, and
installed-wheel obligations in one serial command list. The list remained a
good completeness oracle, but every local closeout and failed PR retry paid its
entire critical path. Local measurements showed that ordinary pytest, isolated
G11 cases, package build, and post-build wheel verifiers could overlap without
removing an obligation.

The scheduling choice needed more than one fast local run. It had to preserve
every serial command, bind the exact inputs and environment, fail closed on
missing or ambiguous evidence, and reproduce on hosted Python 3.12 runners.

## Options Considered

- Keep the complete serial gate as the default.
- Use `pytest-xdist` with two or four file-level workers.
- Use test-level `pytest-xdist` despite nested G11 child processes.
- Keep only static pytest/G11 shards and leave the rest serial.
- Use a four-worker claim/evidence DAG.
- Use a three-worker claim/evidence DAG with static G11 shards, explicit
  dependencies, a sufficiency receipt, and the exact serial battery retained
  as the rollback oracle.
- Promote changed-path routing or cross-run receipt reuse at the same time.

## Decision

Use the full profile of the owner-local claim/evidence graph as the default
implementation of root `scripts/release_check.py` and the GitHub
`Repo Validation` gate.

Keep three workers as the manifest default. Preserve the complete ordered
`COMMANDS` battery in `scripts/release_check.py` and expose it unchanged through
the documented serial mode and `AOA_SDK_VALIDATION_MODE` rollback setting.
Retain a manual GitHub serial-oracle workflow for repeated comparison and
rollback evidence.

The default graph remains full-scope and fail-closed. Changed-path routing stays
shadow-only, and cross-run receipt reuse remains disabled. Neither may
authorize landing without a separate accepted decision and no-miss evidence.

## Rationale

Three same-tree hosted pairs passed both candidates and every graph receipt
reported 14/14 required evidence units, stable repository and manifest
identity, no unreadable inputs, and no integrity blocker. The compared core
steps were `96/135/137` seconds for serial and
`57.545/65.899/67.373` seconds for the graph. Median duration changed from
`135` to `65.899` seconds, a 51.2 percent reduction. Median whole-job duration
changed from `193` to `130` seconds while the workflow prerequisites remained
the same.

Four graph workers and four `xdist` workers could be faster locally, but used
materially more CPU or memory. Three graph workers gave the stronger measured
latency/resource balance. Static sharding is retained inside that graph rather
than treated as a competing authority.

## Consequences

- Local and hosted callers of the standard release command receive bounded
  parallel scheduling without selecting a weaker profile.
- CI retains an atomic full-scope receipt, including node outcomes, command and
  output digests, exact input identities, and nested verifier checkout
  identities.
- Parallel execution increases instantaneous resource demand. The default is
  capped at three workers, and host-managed local runs still require resource
  admission where applicable.
- The manifest and its regressions become part of the owner validation
  contract; any serial command omitted by the graph is a test failure.
- The serial route remains executable and reviewable, but is no longer paid on
  every normal session or PR.
- This decision authorizes only the `aoa-sdk` owner gate. It does not grant a
  central `aoa-evals` verdict or authorize sibling repositories to copy SDK
  claims, shards, or dependencies.

## Source Surfaces

- `scripts/release_check.py`
- `.github/workflows/repo-validation.yml`
- `.github/workflows/validation-evidence-shadow.yml`
- `mechanics/release-support/parts/validation-evidence-graph/config/validation_graph.json`
- `mechanics/release-support/parts/validation-evidence-graph/scripts/validation_graph.py`
- `mechanics/release-support/parts/validation-evidence-graph/tests/test_validation_graph.py`
- `evals/reports/aoa-validation-evidence-graph.report.md`

## Follow-Up Route

Verify the promoted gate after merge and in fresh agent sessions. Reuse the
claim/evidence ABI, not the SDK command list, when each sibling owner performs
its own baseline, shadow comparison, rollback design, and admission decision.
Keep partial routing and cross-run reuse behind their remaining seeded-change,
freshness, and tamper evaluations.

## Verification

Run the graph contract tests, decision-index builder/check, mechanics topology,
local eval-port validator, full graph with a retained receipt, the manual
serial oracle when comparison is needed, GitHub `Repo Validation`, and a
post-merge main-branch run. Hosted comparison evidence and its proof ceiling
are recorded in the SDK-local eval report.
