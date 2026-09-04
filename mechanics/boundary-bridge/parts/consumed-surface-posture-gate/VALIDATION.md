# Consumed Surface Posture Gate Validation

Repository-wide source-home, workspace-capsule, package-build, release, and full-suite checks are owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks) and [its release-facing lane](../../../../VALIDATION.md#release-facing-and-full-owner-checks).

Run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests
python -m mypy src/aoa_sdk/control_plane/routing
python mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_g5_canonical_wheel.py
python mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/measure_routing_succession_e1.py --check
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_succession_x1_consumer_zero_candidate.py
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_succession_x1_consumer_zero_report.py
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_succession_x2_archive_closeout.py
```

The M1 shadow, G4, G5 candidate, and G5 release-candidate probes remain
available for explicit historical replay. They are not part of ordinary
post-G5 validation and require their exact immutable predecessor/input roots.

`test_consumed_surface_compatibility_gate.py` also proves the
`abyss-stack` diagnostic catalog resolves through the part-local
diagnostic-spine path and does not fall back to the old root `generated/`
copy.
`test_workspace_control_plane_compatibility.py` proves the SDK compatibility
gate fails closed when the workspace control-plane artifact identity stops
being an object.
`test_routing_succession_r0_baseline.py` proves the proposed succession
baseline stays pinned, covers every root producer output, preserves the
false-green runtime and trust-denial findings, and has no unclassified G0
dependency.
`test_routing_succession_r1_target_operating_model.py` proves accepted target
ownership remains distinct from live authority, every lifecycle operation has
one owner, the owner-only switch preserves the routing ABI and namespace, and
archive execution remains operator-gated.
`test_routing_succession_r2_control_plane_contracts.py` proves strict JSON
round-trip, one contract family across all three golden scenarios, a closed
lifecycle graph, exact snapshot/ABI/approval scope, command replay
idempotency, event-chain integrity, runtime-neutral plans, and separation of
runtime success from eval, memory, and closeout.
`test_routing_succession_r3_migration_rehearsal.py` proves all fourteen
artifacts stayed byte/schema/count compatible, the installed SDK wheel built
without an `aoa-routing` checkout, rollback remained available, the disposable
candidate was removed, M1 integration debt stayed explicit, and G3 did not
silently authorize G5.
`test_routing_shadow_producer.py` and `test_routing_shadow_bundle.py` prove the
typed compiler, negative cases, deterministic reconstruction, strict packaged
schemas, dual-producer provenance, non-publishing guard, and substitution
denial. They also prove that compact fixture archives reject traversal and
link members before test extraction. `verify_routing_shadow_wheel.py` proves
those surfaces are present and functional in the built wheel rather than only
in the source checkout.
`test_routing_succession_g4_evidence.py` proves G4 remains shadow-only, pins
all fourteen full-corpus input refs and canonical artifact hashes, requires
the full 170-route replay before the runtime dry run, keeps runtime provenance
fail-closed, and accepts the current canonical owner-shortlist `guard` kind.
`verify_routing_succession_g4.py` is the environment-bound G4 integration
gate. It rebuilds and clean-installs v0.6.0, runs compact and full-corpus
determinism/parity, verifies package trust and predecessor rollback, and loads
an isolated 23-file runtime mirror without touching the live deployment.
`test_routing_g5_candidate.py` proves the explicit producer posture changes
only SDK producer/return-route identity, preserves payload and ABI shape,
requires exact clean Git refs, binds all assembly subjects and hashes, rejects
substitution or canonical-looking output roots, and keeps every G5 authority
flag false. It also proves the manifest exposes only `manually-verified` as
an active registry state and uses the distinct `runtime_canary` intent, while
keeping superseded and revoked terminal exits. `verify_routing_g5_candidate_wheel.py` proves the installed wheel
contains the candidate builder, the twenty-one historical G5 routing schemas
plus four post-switch Agon bridge schemas, two runtime boundary documents, the
complete fourteen-artifact assembly, and the exact 23-file runtime-required
subset.
`test_routing_g5_release_candidate.py` proves the release envelope binds the
exact nested candidate, 29 release subjects, deterministic archive, public
release lifecycle, explicit admission profile, and all-false G5 authority.
The installed release-candidate wheel probe proves the same package data and
archive behavior without checkout-local imports.
`test_routing_g5_canonical.py` proves the G5 receipt and provenance bind exact
authority, immutable public-release bytes, the runtime contract, deterministic
archive output, and the archive stop line. It rejects digest, authority, and
output-root substitution. The installed canonical wheel probe proves both new
schemas and the canonical builder are shipped package data, while keeping
`live_cutover_executed` and `archive_authorized` false.
`test_routing_succession_e1_cost_comparison.py` recomputes workflow checkout
and probe counts from pinned Git refs, joins retained T1/G11 receipts, rejects
latency/token overclaims, recomputes four exact landed main-run durations, and
requires G13 to expose rather than hide the 23.1% median runner-time
regression.
`test_routing_shadow_producer.py` also validates the SDK-owned
composite-stress compatibility witness and the post-switch consumer contract,
including its explicit predecessor-checkout prohibition and packaged Agon
bridge route.
`test_routing_succession_x1_consumer_zero_candidate.py` validates exact
candidate refs, complete accounting for the sixteen R0 consumers and one
later discovery, zero active direct-checkout dependencies in the candidate
set, classified residual references, and the still-false landed,
compatibility-exit, rollback-retirement, and archive gates.
`test_routing_succession_x1_consumer_zero_report.py` validates the final 17
consumer and 24-current-head census, thirteen exact owner landings, six SDK
main cycles at or after the SDK migration landing plus three separately
classified pre-migration baseline cycles, `aoa-kag` post-merge success, the
clean immutable-tag release
replay, exact wheel install/upgrade/downgrade/restore, three post-repair Agent
OS cycles, live SDK-only rollback, mixed E1 result, all six compatibility-exit
criteria, and the successful main validation containing the landed X1 report.
It also proves the schema keeps archive readiness distinct from authority and
rejects live-runtime or report archive authorization and any executed
irreversible predecessor action.
`test_routing_succession_x2_archive_closeout.py` pins the immutable X1 bytes,
independently validates the durable raw-session operator approval receipt and
its exact request/response record digests, requires X2 to bind that receipt by
path and SHA-256, and validates the final predecessor landing and release,
preserved public GitHub archive state, SDK-canonical post-archive runtime
health, and `aoa-kag` provider succession. It also keeps the old KAG runtime
slice visible as a non-blocking `source_unavailable` projection residual
instead of relabeling it as current or treating it as an active checkout
dependency.

For full Boundary Bridge coverage, also run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector.py mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/tests/test_technique_promotion_readiness_reader.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff_cli.py
```

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
