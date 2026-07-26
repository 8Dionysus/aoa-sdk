# Routing Succession G5 Owner Switch

## Result

`aoa-sdk` now carries the source contract for the single canonical routing
producer. G5 is expressed by a receipt-bound `v0.8.0` release envelope, not by
changing the routing corpus or inferring authority from the earlier public
release.

The switch authorizes producer ownership. It does not claim that the live
runtime has already consumed the artifact, that consumers have reached zero,
or that `aoa-routing` may be archived.

## Trust Roots

The switch joins three exact, independently owned facts:

| Claim | Exact authority |
| --- | --- |
| Reviewed routing bytes | public `v0.7.0` release-candidate asset, SHA-256 `adf38173306baef7fc47595fc7f44b46bb107fbc48b493adf4b665a22520bee2` |
| Canonical producer authorization | `v0.8.0` SDK source plus `succession/routing-g5-owner-switch.json` |
| Runtime cutover contract | `abyss-stack@fac82c75d860dd2433cfc1e391f4b6ba117425d7`, `ABYSS-STACK-D-0086` |

The earlier release asset remains the byte-parity root because it already
exists independently of the final receipt. The canonical envelope is a
different artifact with its own source ref and attestation. This avoids
embedding an archive digest inside that same archive.

## Canonical Envelope

`aoa_sdk.control_plane.routing.canonical` rebuilds the candidate from the exact
`v0.7.0` producer inputs and rejects the switch unless every one of the 27
assembly members is byte-identical to the public asset.

It then adds:

- `succession/routing-g5-owner-switch.json`;
- `succession/routing-g5-canonical-provenance.json`;
- `artifact.bundle.json` using profile `aoa-sdk-g5-canonical`.

The owner-switch receipt binds:

- the exact SDK source ref, version `0.8.0`, and
  `aoa_routing_thin_router_v1`;
- predecessor `aoa-routing@97f60de1b5992ef6bf5ff0f051bd452d940d9a85`
  with rollback posture retained;
- the public `v0.7.0` release ref, source ref, asset name, and digest;
- the exact `abyss-stack` runtime contract;
- the compatibility-window start date;
- all G5 authority flags and the archive stop line.

## Authority

G5 sets:

- `canonical_producer_switch_authorized=true`;
- `sdk_canonical=true`;
- `live_runtime_mutation_authorized=true`;
- `predecessor_maintenance_only=true`;
- `compatibility_window_started=true`;
- `archive_authorized=false`.

`live_runtime_mutation_authorized` means the runtime owner may execute its
separate receipt-gated cutover after stronger-owner admission. Canonical
release provenance still records `live_cutover_executed=false`.

## Ordered Handoff

1. Publish and attest the exact `v0.8.0` canonical archive.
2. Add the exact `aoa-sdk-g5-canonical` admission policy in `abyss-machine`.
3. Verify, promote, and materialize the exact published artifact.
4. Execute the `abyss-stack` cutover from `ABYSS-STACK-D-0086` and record its
   separate runtime receipt.
5. Land the paired `aoa-routing` M3 compatibility/maintenance receipt.
6. Measure the compatibility window and consumer-zero conditions.

The Agent OS Runner is a later release and must not be hidden inside this owner
switch.

## Archive Stop Line

`aoa-routing` stays available for compatibility, security, rollback, and
deprecation support. Repository archival remains forbidden until consumer-zero
and compatibility exit are proven and the operator gives separate exact
approval.

## Validation

The focused source tests cover receipt/schema binding, immutable public-release
parity, deterministic canonical archives, authority substitution, digest
substitution, and output-root safety. The installed-wheel probe proves the
builder and both new schemas are package data. The release workflow reconstructs
the exact full-corpus envelope, verifies its checksum, and creates a GitHub
attestation before the stronger-owner and runtime handoffs begin.
