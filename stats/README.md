# aoa-sdk local stats port

This directory exposes statistical questions whose domain meaning belongs to
`aoa-sdk`. It uses the shared `aoa-stats` measurement grammar without moving
compatibility meaning or runtime truth into the central organ.

## Current reference measurement

| Measurement | Question | Reference value |
| --- | --- | --- |
| `aoa-sdk/federation-compatibility-version-negotiation-ratio` | What fraction of current federation compatibility rules declare explicit version negotiation? | `66 / 69` at policy blob revision `1e1bebc72eea313be58cf3b00f4d54ffcf589780` |

The reference packet is a census of `SURFACE_COMPATIBILITY_RULES` in
`src/aoa_sdk/compatibility/policy.py`. The three current strict-shape,
versionless rules remain visible in the denominator:

- `aoa-playbooks.playbook_activation_surfaces.min`;
- `aoa-playbooks.playbook_federation_surfaces.min`;
- `aoa-memo.checkpoint_to_memory_contract.example`.

The separate RPG compatibility registry is outside this population; this
measurement does not silently generalize from the federation policy map to
every typed surface reader in the repository.

## Authority

The ratio reports declared SDK negotiation posture only. It does not prove
sibling availability, freshness, semantic compatibility, runtime
compatibility, adoption, successful use, or owner acceptance. `aoa-stats` may
validate and compose the packet without redefining SDK compatibility meaning.

## Surfaces

- `port.manifest.json` declares the local question, measurement contract, and
  export.
- `packets/federation-compatibility-version-negotiation-ratio.reference.json`
  records the evidence-linked reference observation.
- `src/aoa_sdk/compatibility/policy.py` remains the immediate owner evidence.
- `docs/versioning.md` remains the authored explanation of compatibility
  posture.
