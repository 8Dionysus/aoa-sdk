# AGENTS.md

## Applies To

This card applies to `sdk/runtime-entry/`.

## Role

`sdk/runtime-entry/` names Workspace, Codex, and reviewed closeout entry
posture.

It keeps entry surfaces below runtime authority. The SDK may inspect, build
packets, enqueue reviewed work, or orient Codex; it must not become a runtime
worker.

## Read Before Editing

1. root `AGENTS.md`
2. `sdk/AGENTS.md`
3. `sdk/source_home.manifest.json`
4. `sdk/runtime-entry/README.md`
5. the target family README
6. `.aoa/AGENTS.md` for workspace metadata changes
7. the owning runtime-seam, codex-projection, or checkpoint mechanic route

## Boundaries

- Do not make path guessing stronger than `.aoa/workspace.toml`.
- Do not turn Codex orientation into a Codex runtime.
- Do not treat checkpoint or closeout artifacts as memory, proof, progression,
  or owner verdicts.
- Do not create hidden daemon behavior from entrypoint posture.

## Validation

```bash
python scripts/validate_sdk_source_home.py
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python scripts/validate_mechanics_topology.py
```

## Closeout

State whether the route changed workspace context, Codex entry posture,
closeout entry posture, implementation, or mechanic validation.
