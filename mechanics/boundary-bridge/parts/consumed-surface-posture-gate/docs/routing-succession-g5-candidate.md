# Routing Succession G5 Candidate

## Status

This document defines the executable `aoa-sdk` producer candidate that may be
presented to the artifact-trust owner and an isolated runtime canary before the
G5 owner-switch receipt.

It is deliberately not the G5 receipt. `aoa-routing` remains the one canonical
producer, its conditional M2 handoff remains in force, and the compatibility
window has not started.

## Why This Stage Exists

G4 proved that the released SDK shadow producer can reproduce the predecessor
across the full 170-route corpus and that the runtime consumer can load the
content. It could not prove native SDK producer identity: every shadow artifact
correctly still named `aoa-routing`, and the isolated runtime mirror had neither
an SDK source ref nor durable trust admission.

The G5 candidate closes that evidence gap without collapsing build, trust,
runtime, and ownership into one action. It creates an SDK-identified artifact
that stronger owners can evaluate while all switch authority stays false.

## Producer Postures

The package exposes two explicit producer postures:

| Posture | Artifact identity | Permitted use |
| --- | --- | --- |
| `predecessor_compatible` | `aoa-routing` | M1/G4 byte-compatible shadow and rollback evidence |
| `sdk_g5_candidate` | `aoa-sdk` | non-publishing artifact-trust review and isolated or explicitly authorized canary |

The default validator posture remains `predecessor_compatible`. Candidate
identity must be selected explicitly.

The candidate changes only:

- the two producer artifact-identity objects;
- owner-qualified routing producer fields named `owner_repo`, `source_repo`,
  `surface_repo`, or `target_repo` whose exact prior value is `aoa-routing`.

It preserves:

- all fourteen public output filenames;
- all schema identifiers and ABI epochs;
- `aoa_routing_thin_router_v1`;
- route counts, object identifiers, source-owned meaning, and next-hop payload;
- deterministic reconstruction from the same owner-qualified inputs.

Schema compatibility temporarily admits both known producer owners. The strict
validator still requires the exact owner for the selected posture, so the
schema widening cannot silently turn a predecessor artifact into an SDK
candidate or vice versa.

## Candidate Assembly

`python -m aoa_sdk.control_plane.routing.candidate` builds a fresh standalone
assembly outside the SDK repository:

```text
artifact.bundle.json
docs/                                      2 runtime boundary documents
generated/                                14 routing artifacts
schemas/                                  11 runtime-required schemas
succession/routing-g5-candidate-provenance.json
```

The 27 content subjects are the complete fourteen-artifact routing family,
eleven runtime schemas, and two runtime-boundary documents. The current
`abyss-stack` runtime-required set is an exact 23-file subset: ten generated
surfaces, eleven schemas, and two documents. Carrying all fourteen generated
outputs keeps artifact identity and rollback evidence complete even though the
runtime loads only ten of them.

The candidate builder fails closed unless:

- all fourteen producer inputs are clean Git worktrees at the exact full refs
  recorded in provenance;
- `sdk_source_ref` equals the `aoa-sdk` input ref;
- the output root is absent or empty, is not a symlink, is not the SDK
  repository, and is not named `generated`;
- every output matches a deterministic rebuild under `sdk_g5_candidate`;
- schemas, content hashes, assembly hashes, manifest subjects, ABI subject, and
  provenance agree;
- all G5 authority flags remain `false`.

The packaged wheel probe creates clean Git-bound fixture inputs and proves that
the installed distribution, not checkout-local imports, can build and validate
the candidate with its schemas and runtime documents.

## Trust and Runtime Route

The candidate carries
`artifact_class: thin_routing_readmodel_bundle` and an OS Abyss artifact
manifest. Its required controls remain:

- `abi_signature`;
- `sbom`;
- `slsa_in_toto`.

`abyss-machine` is the stronger artifact-trust owner. It must admit the exact
SDK producer/source combination, produce durable evidence, materialize the
verified subjects, and return a consumer-intent-specific trust verdict.

`abyss-stack` is the runtime consumer. It must consume the materialized subject
set and durable trust record, preserve the exact SDK source ref and subject
digest, prove isolated and authorized canary behavior, and retain the
predecessor rollback path. A copied directory, a green SDK test, a sidecar
build, or a schema-valid runtime mirror is not admission.

The owner sequence is:

1. land and release the non-publishing SDK candidate capability;
2. update the stronger artifact policy without switching canonical producer;
3. build and admit one exact SDK candidate artifact;
4. validate the isolated runtime consumer and an explicitly authorized canary;
5. land the exact SDK G5 receipt only if source, trust, runtime, rollback, and
   consumer evidence all agree;
6. only then mark `aoa-routing` maintenance-only and start the compatibility
   window.

At every step there is exactly one canonical producer.

## Authority Stop Line

This candidate does not authorize:

- canonical SDK publication;
- live runtime mutation;
- G5;
- predecessor retirement or maintenance-only posture;
- compatibility-window start;
- consumer-zero;
- repository archival.

Archive execution remains subject to exact, explicit operator approval after
all separate exit conditions pass.

## Validation

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_g5_candidate.py
python -m mypy src/aoa_sdk/control_plane/routing
python -m build
python mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_g5_candidate_wheel.py
```
