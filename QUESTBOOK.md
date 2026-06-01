# aoa-sdk Questbook

This is the human index for durable SDK obligations that should survive the
current diff.

Source quest records live in `quests/<lane>/<state>/`. This file summarizes
the open route; it does not author quest meaning. Quest source-store law lives
in `mechanics/questbook/`.

## Open Lanes

| Lane | Source route | Purpose |
| --- | --- | --- |
| Agon helper candidates | `quests/agon/ready/` | requested-only SDK helper candidate follow-through below Agon owner authority |

## Open Agon Follow-Through

- `AOA-SDK-Q-AGON-0001-recurrence-adapter-registry`
- `AOA-SDK-Q-AGON-0002-prebinding-review-lanes`
- `AOSDK-Q-AGON-0001-state-packet-helper-candidates`
- `AOSDK-Q-AGON-0002-ccs-helper-candidates`
- `AOSDK-Q-AGON-0003-vds-helper-candidates`
- `AOSDK-Q-AGON-0003-retention-rank-helper-candidates`
- `AOSDK-Q-AGON-0003-epistemic-sdk-helpers`
- `AOSDK-Q-AGON-0004-duel-kernel-sdk-bindings`
- `AOSDK-Q-AGON-0005-mechanical-trial-sdk-helpers`
- `AOSDK-Q-AGON-0005-slc-sdk-helpers`
- `AOSDK-Q-AGON-0006-kag-sdk-helpers`
- `AOSDK-Q-AGON-0006-sophian-sdk-helpers`

## Boundaries

- Roadmap direction stays in `ROADMAP.md`.
- Helper contracts stay in their owning `mechanics/agon/parts/*` homes.
- Quest source placement stays in root `quests/`.
- Agon doctrine, verdicts, rank, retention, KAG promotion, and Tree of Sophia
  canon stay outside `aoa-sdk` helper authority.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py --strict-advisory --fail-on-untracked
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
```
