# Runtime Seam Roadmap

This roadmap owns future pressure for the SDK Runtime Seam mechanic.

## Current Contour

Runtime Seam owns workspace root resolution, portable workspace bootstrap,
control-plane capsule posture, and source/runtime mirror boundaries. It keeps
local topology explicit without turning runtime mirrors into source truth.

## Next Work

- Keep workspace resolution manifest-driven and fail-closed on ambiguous paths.
- Keep runtime mirrors visibly weaker than source checkouts.
- Keep control-plane capsule generated from source surfaces and validators.
- Keep portable bootstrap bounded to local-first setup, not deployment truth.

## When Time Comes

- Add runtime-seam parts only when a repeated seam cannot stay inside root
  resolution, bootstrap, capsule, or mirror boundary.
- Add remote adapter behavior only after local source/runtime separation stays
  stable.

## Out Of Scope

- runtime deployment authority;
- hidden path fallbacks;
- source ownership transfer to mirrors;
- live service lifecycle truth.

## Update Trigger

Update this roadmap when workspace resolution, mirror boundary, capsule
posture, bootstrap semantics, or future runtime seam depth changes.
