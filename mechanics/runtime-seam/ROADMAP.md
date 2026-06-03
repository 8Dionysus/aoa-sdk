# Runtime Seam Roadmap

Runtime Seam is the SDK route for keeping local workspace topology explicit. It
separates source checkouts, runtime mirrors, bootstrap posture, and generated
control-plane capsules without turning runtime mirrors into source truth or
deployment authority.

## Current Contour

- Keep workspace root resolution, portable workspace bootstrap, control-plane
  capsule posture, and source/runtime mirror boundaries routed through active
  `parts/`.
- Keep workspace resolution manifest-driven and fail-closed on ambiguous paths.
- Keep runtime mirrors visibly weaker than source checkouts.
- Keep the control-plane capsule generated from source surfaces and validators.
- Keep portable bootstrap bounded to local-first setup, not deployment truth.

## Next Work

- Tighten manifest and override contracts where repeated workspace layouts prove
  stable.
- Keep source/runtime mirror language aligned across docs, config, generated
  capsule, and workspace discovery code.
- Preserve local-first setup without smuggling deployment lifecycle or runtime
  ownership into the SDK.

## When Time Comes

- Add runtime-seam parts when a repeated seam cannot stay inside root
  resolution, bootstrap, capsule, or mirror boundary.
- Add remote adapter behavior only after local source/runtime separation stays
  stable.
- Add richer generated topology views only when builders and validation remain
  stronger than the view.

## Out Of Scope

- Runtime deployment authority.
- Hidden path fallbacks.
- Source ownership transfer to mirrors.
- Live service lifecycle truth.
- Host setup outside explicit local-first contracts.
