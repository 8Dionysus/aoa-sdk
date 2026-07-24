# Federation Entry ABI

The routing federation-entry namespace remains
`aoa_routing_federation_entrypoints_v2` during the producer-owner succession.
The public filename remains `generated/federation_entrypoints.min.json`.

Source repositories own meaning. The routing control plane owns deterministic
navigation metadata only.

An `aoa-sdk`-identified artifact may be used before G5 only as an explicit
non-publishing canary. It does not become the canonical routing surface until
the separate G5 receipt binds the exact SDK source ref, artifact-trust record,
runtime mirror, rollback evidence, and predecessor handoff.

The stable entry-card fields remain:

- `kind`
- `id`
- `owner_repo`
- `title`
- `capsule_surface`
- `authority_surface`
- `next_actions`
- `fallback`
- `risk`
- `next_hops`

`capsule_surface` and `authority_surface` remain owner-qualified references.
An SDK producer identity does not transfer agent, playbook, KAG, runtime,
proof, memory, skill, technique, stats, or Tree of Sophia authority into the
SDK.

Runtime consumers must verify the artifact ABI, exact source ref, subject
digest, required trust controls, and source-owned next hops before admitting
the bundle. A copied file tree, candidate receipt, build result, or successful
schema check is not a trust verdict or owner switch.

