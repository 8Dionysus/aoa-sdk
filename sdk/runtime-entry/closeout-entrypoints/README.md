# Closeout Entrypoints

Role: route checkpoint, A2A return, and reviewed closeout entry posture.

Input: checkpoint capture, closeout request assembly, reviewed inbox behavior,
A2A return packets, and closeout-context carry.

Output: implementation route, checkpoint mechanic route, owner handoff, or
decision record.

Owner: `sdk/runtime-entry/AGENTS.md` and
`sdk/source_home.manifest.json#closeout_entrypoints`.

Next route: `src/aoa_sdk/checkpoints/`, `src/aoa_sdk/closeout/`,
`src/aoa_sdk/a2a/`, and `mechanics/checkpoint/parts/`.

Stop line: do not treat checkpoint or closeout artifacts as memory, proof, or
owner verdicts.
