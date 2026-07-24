# Routing Succession R3 Migration Rehearsal

Status: G3 passed; the disposable implementation was removed. M1 shadow
implementation is authorized, but no producer switch, canonical publication,
runtime mutation, or repository archive is authorized.

Machine-readable evidence:
[`../evidence/routing-succession-r3-migration-rehearsal.json`](../evidence/routing-succession-r3-migration-rehearsal.json).

## Result

The predecessor producer at `7e2fe467` was rebuilt from a pinned thirteen-repo
input set. Its fourteen outputs matched the checked-in routing bundle
byte-for-byte. Only the two producer modules, 5,591 source lines in total, were
then placed under the candidate SDK topology:

```text
src/aoa_sdk/control_plane/routing/
  core.py
  producer.py
```

The only implementation differences were the package-relative import, SDK
repository-root resolution, and candidate-only module documentation. The
existing `src/aoa_sdk/routing/` consumer facade was untouched. No predecessor
mechanics tree, history, docs mesh, generated directory, or repository
scaffolding moved.

The source candidate, then an installed `aoa-sdk` wheel in a fresh virtual
environment, each rebuilt all fourteen outputs with byte parity. The wheel was
executed from a dependency root that had no `aoa-routing` checkout. The
predecessor schema and semantic validator accepted the SDK output, and the
predecessor producer rebuilt the same bundle again after the trial. That is
the rollback proof.

## Provenance

Before G5, byte parity and authority truth require the embedded owner and
producer fields to remain `aoa-routing` and `scripts/build_router.py`. Changing
those fields during shadow generation would create a false ABI difference and
prematurely claim authority.

M1 must therefore add a sidecar receipt naming both exact producer refs while
leaving the fourteen compatibility artifacts unchanged. The embedded owner and
producer identity changes only in the G5 owner-switch PR.

## Integration Debt Found by the Rehearsal

The migration is feasible, but the copied implementation is not yet an
SDK-quality production package:

- `PyYAML>=6.0` is a real runtime dependency that the SDK must declare;
- `types-PyYAML` is required for the development type-check lane;
- the predecessor script carries twenty code-level mypy errors;
- schemas, validators, fixtures, negative cases, and package-data validation
  still belong to M1;
- installed-wheel validation and dual-producer provenance must become CI
  gates.

The observed mypy total was twenty-one errors: twenty inherited code typing
errors and one missing stub error. This does not invalidate G3 because R3
tests feasibility, parity, clean construction, consumers, provenance strategy,
and rollback. M1 may not merge or release until those integration debts are
closed.

## Exact Landing Order

1. Land `SDK_M1_SHADOW` with the packaged producer, schemas, validators,
   fixtures, negative tests, parity CI, typing fixes, and sidecar provenance.
2. Publish `SDK_M1_SHADOW_RELEASE` so cross-repo tests pin immutable code.
3. Land `ROUTING_M1_PARITY_CONSUMER`; the predecessor remains canonical and
   compares its output with the released SDK shadow.
4. Land `SDK_G4_EVIDENCE` only after clean install, deterministic rebuild,
   runtime-mirror dry run, trust, consumer, and parity checks.
5. Land `ROUTING_M2_CONDITIONAL_HANDOFF`; it freezes new features but remains
   canonical until the named SDK G5 merge.
6. Land `SDK_M2_G5_SWITCH`, which alone changes canonical production and
   embedded producer provenance.
7. Land `ROUTING_M3_COMPATIBILITY` and remove duplicate active mechanics while
   preserving rollback through the compatibility window.

This order avoids both a producer gap and two simultaneously canonical
producers.

## Cleanup

The exact disposable SDK and routing worktrees were removed after the hashes,
counts, validation results, rollback result, and recreation recipe had been
captured. Their uncommitted candidate code was intentionally discarded. It can
be recreated from the two pinned predecessor modules plus the three recorded
candidate differences; no user worktree or canonical file was removed.
