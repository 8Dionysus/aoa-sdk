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

`aoa route resolve|explain|validate` exposes the C1 Agent OS route contour.
`resolve` verifies the explicit SDK-canonical runtime bundle and pinned owner
projection before producing a decision. `explain` accounts for the existing
decision without rerouting. `validate` checks typed shape and, when supplied,
exact parent binding. All three remain non-executing and report no fallback.
There is no `aoa route compile` command until C2.

`aoa organs validate|compile|catalog|inspect|capability|plan` exposes the
organ-access contract without runtime mutation. `compile --output` is the only
projection write and requires an explicit destination. `plan` always emits
candidate intent with `execution_authorized=false`; no CLI command provisions
credentials, starts a process, calls an owner tool, or promotes registry
maturity.
