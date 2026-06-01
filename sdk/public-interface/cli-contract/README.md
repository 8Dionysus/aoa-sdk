# CLI Contract

Role: route CLI command posture as public SDK control-plane entrypoints.

Input: command names, output posture, flags, workspace entry behavior, release
helpers, checkpoint commands, or compatibility inspection behavior.

Output: implementation route, CLI test route, mechanic route, or release gate.

Owner: `sdk/public-interface/AGENTS.md` and
`sdk/source_home.manifest.json#cli_contract`.

Next route: `src/aoa_sdk/cli/`, `mechanics/runtime-seam/`,
`mechanics/checkpoint/`, and `mechanics/release-support/`.

Stop line: do not let CLI convenience bypass owner review, compatibility
checks, or release gates.
