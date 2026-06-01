# AGENTS.md

## Applies To

This card applies to `sdk/` and every nested path until a nearer `AGENTS.md`
narrows the lane.

## Role

`sdk/` is the source-authored SDK home for `aoa-sdk`.

It names what the SDK owns as an SDK: public interface posture, facade
boundaries, runtime entry posture, and distribution promises. It does not
replace the importable Python implementation under `src/aoa_sdk/`, and it does
not replace operation mechanics under `mechanics/`.

## Operating Card

| Field | Route |
| --- | --- |
| role | source home for SDK-owned shape and public control-plane promises |
| input | API posture, facade boundary, runtime-entry, or distribution route pressure |
| output | checked source-home manifest route, branch route card, implementation route, mechanic route, or stronger-owner handoff |
| owner | `sdk/source_home.manifest.json`, this card, and nearest branch `AGENTS.md` |
| next route | `sdk/README.md`, `sdk/SDK_SHAPE.md`, target branch `AGENTS.md`, implementation surface, mechanic part, or decision record |
| tools | `scripts/validate_sdk_source_home.py`, `scripts/validate_nested_agents.py`, release gate |
| validation | this card's `Validation` section plus target implementation or mechanic checks |

## Route Stack

- Above: root `AGENTS.md` owns repository identity, owner boundaries, and
  broad validation posture.
- Here: `sdk/README.md` owns the source-home map,
  `sdk/SDK_SHAPE.md` owns the human shape contract, and
  `sdk/source_home.manifest.json` owns the checked family topology.
- Below: branch cards own public-interface, facade-boundary, runtime-entry,
  and distribution route law.

## Read Before Editing

Read:

1. root `AGENTS.md`
2. `DESIGN.md`
3. `DESIGN.AGENTS.md`
4. `sdk/README.md`
5. `sdk/SDK_SHAPE.md`
6. `sdk/source_home.manifest.json`
7. the nearest branch `AGENTS.md`
8. the implementation, mechanic, docs, or release surface named by that branch

## Owner Routes

| Need | Owner route |
| --- | --- |
| public API and model posture | `sdk/public-interface/` |
| sibling-reader and truth-label boundary | `sdk/facade-boundary/` |
| workspace, Codex, and closeout entry posture | `sdk/runtime-entry/` |
| package, release, and public support promises | `sdk/distribution/` |
| importable Python implementation | `src/aoa_sdk/` |
| repeatable operation topology | `mechanics/` |
| durable rationale | `docs/decisions/` |

## Route Instead

| Pressure | Do this |
| --- | --- |
| executable Python behavior | edit `src/aoa_sdk/` and run the owning tests |
| single-mechanic artifact payload | route to `mechanics/<parent>/parts/<part>/` |
| public docs or release route doors | route to `docs/` or `mechanics/release-support/` |
| generated companion drift | edit the source input and run the builder |
| sibling source meaning | hand off to the owning sibling repo |
| service runtime behavior | hand off to the runtime owner |

## Compact Rules

- Keep `sdk/` tree-shaped and branch-owned.
- Keep every branch named by operation posture, not implementation package
  structure.
- Keep `source_home.manifest.json` aligned with branch cards and leaf README
  routes.
- Keep `src/aoa_sdk/` as the importable implementation lane.
- Keep `mechanics/` as the repeatable operation topology lane.
- Do not add `PARTS.md` to `sdk/`; `parts` is mechanic vocabulary here.
- Do not move Python modules, tests, schemas, generated readers, or mechanic
  payload into `sdk/` without a separate owner decision and validator.

## Validation

For source-home shape changes, run:

```bash
python scripts/validate_sdk_source_home.py
python scripts/validate_nested_agents.py --strict-advisory --fail-on-untracked
python -m pytest -q tests/test_sdk_source_home.py tests/test_design_surfaces.py
```

If the change touches implementation, mechanics, release, or generated
surfaces, also run the validator named by that owner route.

## Closeout

State which SDK source-home branch changed, whether importable implementation
changed, whether a mechanic route changed, which validators ran, and which
stronger owner remains outside the SDK.
