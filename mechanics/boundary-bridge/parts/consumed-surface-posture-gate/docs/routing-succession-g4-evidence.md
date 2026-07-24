# Routing Succession G4 Evidence

Status: G4 passed in `sdk_shadow` posture. `aoa-routing` remains canonical.
G4 does not publish SDK routing artifacts, mutate the live runtime, authorize
G5, or authorize repository archival.

Machine-readable evidence:
[`../evidence/routing-succession-g4-evidence.json`](../evidence/routing-succession-g4-evidence.json).

## Result

The exact annotated `aoa-sdk` v0.6.0 release was rebuilt, installed into a
fresh virtual environment with `PYTHONPATH` removed, and exercised through the
packaged routing implementation and all seventeen packaged schemas. The
released SDK and the unchanged predecessor each produced fourteen
byte-identical artifacts.

G4 keeps two fixture roles separate:

- the compact M1 release corpus proves installed-package execution,
  dual-producer shadow provenance, deterministic reconstruction, and parity
  with the predecessor without copying the complete owner corpora into the
  repository;
- the full canonical corpus materializes regular files from fourteen exact Git
  refs, including `aoa-sdk@29de1b1`, and proves the installed v0.6.0 producer
  reconstructs the checked-in canonical family at 14/14 exact hashes and 170
  router entries.

The full replay is required before the runtime dry run. The compact corpus has
eight deliberately small registry entries and is not runtime parity evidence.
The canonical archive, current predecessor outputs, two installed SDK rebuilds,
and the predecessor rollback rebuild all agree on the full fourteen-artifact
hash set rooted at:

```text
aoa_router.min.json
f01e3722d675c1776f20ad09e1ac43e5e646de8bdad2858a30d39ba7b7534cb7
170 entries
```

Git archives are read from the supplied repositories without changing their
checkouts. The historical `abyss-stack` input contains `.agents/skills`
symlinks that are outside the producer input contract; the verifier records
and omits only that bounded lane and rejects links anywhere else.

## Runtime Mirror Dry Run

The full-corpus SDK output supplied every generated JSON loaded by the runtime
candidate. Packaged v0.6.0 schemas supplied the schema family. Two documents
that the current `abyss-stack` sync contract still requires, but active
`aoa-routing` has retired, came from exact historical bytes at
`aoa-routing@4d2b29d`.

The repaired runtime-owner surfaces are pinned to
`abyss-stack@fad9f951` (PR 321, post-main run 30072801490). In an isolated
temporary `AOA_STACK_ROOT`, the owner sync wrapper mirrored all 23 required
files, reproduced every candidate hash, and the route API loaded 170 routes.
No path targeted `/srv/AbyssOS/abyss-stack`, and the live runtime was not
mutated.

Content and consumer readiness pass. Provenance and closure intentionally
remain fail-closed because an assembled non-checkout candidate has neither a
native source Git ref nor a durable runtime trust verdict:

```text
mirror_ready       true
consumer_ready     true
provenance_ready   false
closure_ready      false
```

The outer G4 receipt binds the trial to exact SDK, predecessor, runtime-owner,
trust-owner, input, and output refs. It does not impersonate the runtime-native
SDK identity that G5 must establish.

## Package Trust And Consumer Proof

The release source passed the `abyss-machine@4a70f4b0` package artifact trust
controls for ABI signature, SBOM, and SLSA/in-toto evidence using temporary
registry and subject stores. Host trust state was not changed, and package
trust was not presented as live runtime admission.

`aoa-routing@5c7c0e57` remains the canonical consumer and pins the immutable
v0.6.0 release. Its PR 155 and post-main CI independently proved 14/14 parity.
The predecessor implementation paths remain unchanged from `7e2fe467`, and
both compact and full-corpus rollback builds remain byte-identical.

## Contract Drift Closed During G4

The repaired current routing shortlist contains
`object_kind: "guard"`. The SDK contract previously rejected that owner hint,
which broke checkpoint closeout even though routing generation itself was
green. `RoutingOwnerLayerShortlistHint` now admits `guard`, and the G4
regression test parses the exact canonical guard hint. The legacy `seed` value
remains accepted for compatibility; G4 does not reinterpret either owner
kind.

## Reproduction

The owner command and its exact arguments live in
[`../VALIDATION.md`](../VALIDATION.md). The verifier uses a temporary root,
rebuilds the release distributions, creates a fresh environment, materializes
exact Git objects, performs both parity contours, executes package trust,
mirrors the candidate in isolation, and removes the temporary campaign on
exit.

## Next Authorized Stage

G4 permits the named `ROUTING_M2_CONDITIONAL_HANDOFF` preparation only. That
stage may freeze new predecessor features and bind rollback posture, but
`aoa-routing` remains canonical until the later named SDK G5 merge. A G4 pass
does not by itself authorize canonical SDK publication, live mirror mutation,
runtime trust admission, duplicate-mechanics removal, or archival action.
