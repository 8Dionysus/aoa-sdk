# AoA Surface Detection Closeout Handoff

The closeout handoff preserves reviewed candidates without invoking them.

## Boundary

- `sdk.surfaces.build_closeout_handoff(...)` requires `reviewed=True`.
- `aoa surfaces handoff` refuses unreviewed input.
- Surviving items keep their candidate state and `executable_now=false`.
- Capability targets are exact refs for the next owner or agent; they are not
  SDK dispatch instructions.
- Checkpoint notes and persisted reports remain session-local evidence.

Persisted handoffs land under:

```text
aoa-sdk/.aoa/surface-detection/{label}.closeout-handoff.latest.json
```

## Deterministic targets

- any surviving item or reviewed checkpoint cluster may point to the deferred
  `skill.aoa-session-harvest` capability;
- recurring playbook evidence points to the `aoa-playbooks` registry owner;
- unresolved inspection gaps may point to the deferred
  `skill.aoa-session-recovery` capability;
- reviewed playbook or technique promotion pressure points to the
  `aoa-techniques` readiness owner;
- checkpoint upgrade pressure may point to
  `workflow.operations.checkpoint-closeout`.

No target is auto-run, installed, admitted, or promoted by this handoff.
