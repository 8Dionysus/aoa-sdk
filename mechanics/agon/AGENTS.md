# AGENTS.md

## Applies to

`mechanics/agon/`.

## Role

Route the shared Agon mechanic for SDK helper candidates, registries,
recurrence adapters and state-packet bridges. Quest source records route
through root `quests/` and Questbook.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/agon/README.md`
- `mechanics/agon/PARTS.md`
- the nearest part card under `mechanics/agon/parts/`

## Boundaries

- Stay on the control plane.
- Keep Agon helper material candidate-only unless reviewed owner surfaces say
  otherwise.
- Do not turn SDK helper registries into Agon doctrine or verdict authority.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python mechanics/agon/parts/center-law-preview-helpers/scripts/build_agon_ccs_sdk_helper_candidates.py --check
python mechanics/agon/parts/center-law-preview-helpers/scripts/validate_agon_ccs_sdk_helper_candidates.py
python mechanics/agon/parts/state-packet-review-bindings/scripts/build_agon_sdk_state_packet_bindings.py --check
python mechanics/agon/parts/state-packet-review-bindings/scripts/validate_agon_sdk_state_packet_bindings.py
python mechanics/agon/parts/recurrence-adapter/scripts/build_agon_recurrence_adapter_registry.py --check
python mechanics/agon/parts/recurrence-adapter/scripts/validate_agon_recurrence_adapter.py
python mechanics/agon/parts/recurrence-adapter/scripts/build_agon_recurrence_prebinding_review_lanes.py --check
python mechanics/agon/parts/recurrence-adapter/scripts/validate_agon_recurrence_prebinding_review_lanes.py
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/build_agon_duel_kernel_sdk_bindings.py --check
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/validate_agon_duel_kernel_sdk_bindings.py
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/build_agon_mechanical_trial_sdk_helpers.py --check
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/validate_agon_mechanical_trial_sdk_helpers.py
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/build_agon_vds_sdk_helper_candidates.py --check
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/validate_agon_vds_sdk_helper_candidates.py
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/build_agon_retention_rank_sdk_helpers.py --check
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/validate_agon_retention_rank_sdk_helpers.py
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/build_agon_epistemic_sdk_helpers.py --check
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/validate_agon_epistemic_sdk_helpers.py
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/build_agon_kag_sdk_helpers.py --check
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/validate_agon_kag_sdk_helpers.py
python mechanics/agon/parts/school-lineage-campaign-review-helpers/scripts/build_agon_slc_sdk_helpers.py --check
python mechanics/agon/parts/school-lineage-campaign-review-helpers/scripts/validate_agon_slc_sdk_helpers.py
python mechanics/agon/parts/sophian-threshold-review-helpers/scripts/build_agon_sophian_sdk_helpers.py --check
python mechanics/agon/parts/sophian-threshold-review-helpers/scripts/validate_agon_sophian_sdk_helpers.py
python -m pytest -q mechanics/agon/parts/center-law-preview-helpers/tests/test_agon_ccs_sdk_helper_candidates.py mechanics/agon/parts/state-packet-review-bindings/tests/test_agon_sdk_state_packet_bindings.py mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_adapter.py mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_prebinding_review_lanes.py mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_duel_kernel_sdk_bindings.py mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_mechanical_trial_sdk_helpers.py mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_vds_sdk_helper_candidates.py mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_retention_rank_sdk_helpers.py mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_epistemic_sdk_helpers.py mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_kag_sdk_helpers.py mechanics/agon/parts/school-lineage-campaign-review-helpers/tests/test_agon_slc_sdk_helpers.py mechanics/agon/parts/sophian-threshold-review-helpers/tests/test_agon_sophian_sdk_helpers.py
```

## Closeout

Report which Agon helper family, registry, generated companion, or Questbook
source record changed.
