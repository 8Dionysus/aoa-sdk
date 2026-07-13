# Distribution Manifests

This directory holds OS Abyss artifact bundle manifests for built SDK
distribution outputs.

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
