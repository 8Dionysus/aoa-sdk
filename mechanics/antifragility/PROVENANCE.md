# Antifragility Provenance

## Source Surfaces

- Former root `docs/antifragility-control-plane.md` now routes to
  `mechanics/antifragility/parts/stress-posture-dispatch-gate/docs/stress-posture-dispatch-gate.md`.
- Former root `docs/antifragility-closeout-seam.md` now routes to
  `mechanics/antifragility/parts/reviewed-stress-closeout-carry/docs/reviewed-stress-closeout-carry.md`.
- Former root `docs/VIA_NEGATIVA_CHECKLIST.md` now routes to
  `mechanics/antifragility/parts/via-negativa/docs/via-negativa-checklist.md`.
- Former root `tests/fixtures/antifragility/stress_dispatch_input.example.json`
  now routes to
  `mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-request.example.json`.
- Former root `tests/fixtures/antifragility/stress_dispatch_result.example.json`
  now routes to
  `mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-decision.example.json`.
- Former root `tests/fixtures/antifragility/stress_closeout_manifest.example.json`
  now routes to
  `mechanics/antifragility/parts/reviewed-stress-closeout-carry/examples/reviewed-stress-closeout-manifest.example.json`.
- Former root `tests/test_antifragility_public_surface.py` now routes to
  part-local tests under `mechanics/antifragility/parts/*/tests/`.

## Stronger Owners

Owner repositories decide remediation and deletion. `aoa-evals` owns proof
verdicts. The SDK owns bounded control-plane examples, route docs, and
validation for its stress-posture dispatch and reviewed closeout carry.

## Notes

This parent was missing from the first SDK topology draft even though the repo
already had real antifragility surfaces. The active surface is now part-local;
old root paths are provenance only.
