# Stress Posture Dispatch Gate Contract

## Allowed Outputs

- Stress posture disclosure in SDK-visible reports.
- Merged `StressBundle` values from explicit typed signals.
- Narrowed `SummonDecision` task-dispatch results.
- Blocked-action and re-entry conditions.
- Evidence refs for closeout or owner handoff.

## Stop-Lines

- Do not widen permissions because stress context is present.
- Do not select, activate, execute, or mutate skills.
- Do not interpret a blocked action as proof that a runtime enforced it.
- Do not auto-repair owner runtime or degraded surfaces.
- Do not convert routing hints, memo refs, or eval refs into source truth.

## Owner Split

The SDK may carry and disclose the decision. `aoa-skills` owns skill truth;
KAG owns semantic retrieval and task-local composition; the host runtime owns
execution. Affected owners decide remediation, runtime behavior, deletion,
proof acceptance, and durable memory.

## External Source Tokens

Example refs may preserve source-owned stress receipt or routing hint tokens
whose historical handle contains `fallback`, such as
`retrieval-only-fallback`.

Those strings are evidence handles owned by the source or routing repository.
They are not SDK-owned active route names. New SDK-owned stress posture fields,
examples, or routes should use explicit degraded, recovery, source-first, or
alternate-path vocabulary.
