# Routing Succession M1 Shadow Producer

Status: the SDK shadow producer is implemented and package-gated.
`aoa-routing` remains the only canonical producer. The M1 source landing does
not pass G4, switch an owner, publish routing artifacts, mutate a runtime
mirror, or authorize archival action.

## Implemented Slice

The admitted implementation is:

```text
src/aoa_sdk/control_plane/routing/
  core.py
  producer.py
  shadow.py
  validator.py
  schemas/
```

`core.py` and `producer.py` carry the minimal deterministic compiler rehearsed
at R3. The inherited typing debt is resolved without changing the fourteen
artifact bytes. `validator.py` packages schema, deterministic rebuild,
projection-safety, route-count, owner, and ABI checks. `shadow.py` adds the
non-publishing orchestration and its dual-producer provenance sidecar.

The existing `src/aoa_sdk/routing/` package remains the public compatibility
reader. M1 does not route runtime consumers to the new compiler and does not
add an `AoARunner`.

## Shadow Contract

`build_shadow_bundle(...)` requires:

- all fourteen owner-qualified input roots;
- one full Git object ID (SHA-1 or SHA-256) for every input root;
- the exact canonical `aoa-routing` producer SHA;
- the exact SDK shadow producer SHA;
- a fresh empty destination whose resolved final directory is not named
  `generated`.

It writes fourteen byte-compatible routing artifacts and
`routing-shadow-provenance.json`. The compatibility artifacts retain embedded
`aoa-routing` owner and producer identity before G5. The sidecar separately
records:

- repository state `sdk_shadow`;
- publication posture `non_publishing`;
- both producer owners and exact refs;
- the stable `aoa_routing_thin_router_v1` ABI epoch;
- the exact fourteen artifact hashes;
- the exact fourteen input refs;
- a timestamp and authority stop-line.

Validation rejects missing, extra, linked, or substituted artifacts, schema
or date-time format drift, rebuild drift, copied source payload fields,
route-family count drift, embedded owner or ABI drift, changed producer
identities, noncanonical Git object IDs, changed input refs, and changed
artifact hashes.

## Package And CI Proof

The producer declares `PyYAML` and `jsonschema` as runtime dependencies and
ships all seventeen routing schemas as package data. The release battery now:

1. runs all tests, Ruff, and mypy;
2. builds the wheel and source distribution;
3. creates a fresh virtual environment;
4. installs the wheel with no checkout import path;
5. builds and validates the shadow sidecar and all fourteen artifacts;
6. compares the installed-wheel hashes with the pinned predecessor hash
   manifest for the hydrated fixture corpus;
7. verifies that the implementation module and schemas came from
   `site-packages`;
8. continues through the OS Abyss package artifact trust bundle.

The separate `Routing Shadow Parity` CI job checks out the exact predecessor
commit `7e2fe467ad26aa645b61849001a456dda4562ffc`, runs both producers over one
hydrated input corpus, and requires 14/14 byte equality. The predecessor
checkout is test input only; the SDK wheel itself contains the compiler,
validator, and schemas.

The three pinned fixture corpora are stored as deterministic compact archives
instead of thousands of loose duplicate source records. Their test-only
materializer accepts only the named archives and rejects absolute paths,
parent traversal, links, and unsupported tar members before extraction. This
keeps the portable KAG family inside its tracked-size budget without weakening
fixture coverage or admitting an archive extraction path into the SDK wheel.

## Remaining Gate

M1 source landing is followed by an immutable SDK release and a predecessor
consumer PR pinned to that release. G4 still requires the clean-install,
determinism, parity-window, runtime-mirror dry-run, trust, consumer, rollback,
and release evidence to agree. Any unexplained difference stops succession and
must be fixed or become a separate versioned ABI change outside the owner
switch.
