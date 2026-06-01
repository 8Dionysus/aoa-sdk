# Skill Runtime Bridge

This part owns the SDK route from skill-router recommendations and host
inventory signals to explicit runtime actionability reports.

## Role

Input: `aoa skills ...` detection/dispatch pressure, host skill inventory,
runtime session files, and router recommendations.

Output: typed reports that distinguish host-executable, router-only, and
unknown skill recommendations without moving skill meaning into the SDK.

Owner: `aoa-sdk` owns the bridge report shape, CLI/API behavior, runtime
session store, and tests. `aoa-skills` owns canonical skill meaning and export
surfaces.

## Active Surfaces

- [Recommendation Actionability Gap](docs/recommendation-actionability-gap.md)
- [Host Actionability Reporting Design](docs/host-actionability-reporting-design.md)
- [Skill Runtime Bridge Tests](tests/test_skill_runtime_bridge.py)
- [Skill Runtime Bridge CLI Tests](tests/test_skill_runtime_bridge_cli.py)
- `src/aoa_sdk/skills/`
- `src/aoa_sdk/cli/`

## Next Route

Route skill meaning, canonical exports, and availability guarantees to
`aoa-skills`. Keep SDK changes limited to typed bridge behavior and explicit
host actionability labels.
