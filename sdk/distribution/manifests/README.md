# Distribution Manifests

This directory holds OS Abyss artifact bundle manifests for built SDK
distribution outputs and the exact source locks for the public routing G5
release candidate and receipt-bound canonical owner switch.

The manifests are source inputs for `abyss-machine` artifact verification. They
identify the repo-local ABI identity, the built artifact subjects under
`dist/`, and the package metadata source used for SBOM and provenance sidecars.

The package build owner and the release-audit part validator form the
executable validation route. Exact operator checks are maintained in root
`AGENTS.md#verify` and the release-audit part `VALIDATION.md`.

Generated sidecars are written under `dist/abyss-artifact-bundle/`; the local
registry read-model is written under `dist/abyss-artifact-registry/`, and the
materialized subject store is written under `dist/abyss-artifact-subjects/`.
These are ignored build outputs, not source truth. The helper promotes durable
evidence with source and host-managed trust-root metadata, materializes the
package subject store, and checks the consumer `trust-gate` before treating the
bundle as release-ready.

`routing_g5_release_candidate.input-lock.json` is source-authored release
control, not generated evidence. It binds every producer input, the
predecessor, and the stronger-owner verifier to exact Git objects while the SDK
release ref resolves through `SELF`. Its authority block must keep G5 and
normal runtime false. Public archive, attestation, and registry records remain
external publication and trust evidence.

`routing_g5_canonical.input-lock.json` binds the `v0.8.0` SDK source through
`SELF`, the retained predecessor, exact `v0.7.0` public asset and digest, the
runtime owner's `ABYSS-STACK-D-0086` source ref, the original producer-input
refs used for byte parity, the compatibility-window start, and the exact G5
authority flags. It authorizes the producer switch but keeps archive authority
false. Published attestation, stronger-owner admission, runtime execution,
consumer-zero, and archive approval remain external evidence.
