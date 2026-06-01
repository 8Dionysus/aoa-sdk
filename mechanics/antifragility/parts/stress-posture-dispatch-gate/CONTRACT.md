# Stress Posture Dispatch Gate Contract

## Allowed Outputs

- Stress posture disclosure in SDK-visible reports.
- Narrowed dispatch decisions.
- Blocked auto-activation reasons.
- Required review steps.
- Evidence refs for closeout or owner handoff.

## Stop-Lines

- Do not widen permissions because stress context is present.
- Do not auto-activate skills that still require review.
- Do not auto-repair owner runtime or degraded surfaces.
- Do not convert routing hints, memo refs, or eval refs into source truth.

## Owner Split

The SDK may carry and disclose the decision. Owners decide remediation,
runtime behavior, deletion, proof acceptance, and durable memory.

## External Source Tokens

Example refs may preserve source-owned stress receipt or routing hint tokens
whose historical handle contains `fallback`, such as
`retrieval-only-fallback`.

Those strings are evidence handles owned by the source or routing repository.
They are not SDK-owned active route names. New SDK-owned stress posture fields,
examples, or routes should use explicit degraded, recovery, source-first, or
alternate-path vocabulary.
