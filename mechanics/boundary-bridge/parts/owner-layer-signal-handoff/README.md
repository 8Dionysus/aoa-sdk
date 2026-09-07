# Owner-Layer Signal Handoff

## Role

Expose advisory owner-layer surface detection and reviewed closeout handoff
without turning hints into executable truth.

## Input

- `sdk.surfaces.detect(...)` reports
- `aoa surfaces detect` persisted reports
- reviewed session or checkpoint context
- sibling-owned shortlist, stats, and receipt context reads

## Output

- `SurfaceDetectionReport`
- `SurfaceCloseoutHandoff`
- reviewed handoff targets for session-growth or owner follow-through

## Owner

`aoa-sdk` owns the bridge shape and handoff packet. Sibling repos own the
meaning of skills, evals, memo, playbooks, agents, techniques, stats, and
routing.

## Next Route

Reviewed survivors route to checkpoint closeout, owner repos, or sibling
readers. They do not auto-activate here.

## Explicit caller input

`intent_text` is context, not an instruction parser. For example:

```python
report = sdk.surfaces.detect(
    repo_root="/path/to/repo",
    phase="pre-mutation",
    intent_text="Открой каталог навыков и проверь используемую сводку",
    requested_owner_layers=["aoa-skills"],
    consumed_stats_surfaces=["surface_detection_summary"],
)
```

Use `declared_signals` for caller-assessed `proof-need`, `recall-need`,
`scenario-recurring`, `role-posture`, or `repeated-pattern`; the last still
requires checkpoint or closeout phase. These assertions remain below owner
review. A topic hint has empty `signals`, low confidence, no harvest targets,
and no positive checkpoint pressure.

The CLI offers repeatable `--request-owner-layer`, `--declare-signal`, and
`--consumed-stats-surface`. `checkpoint append` also accepts the first two;
the Python checkpoint API can accept the complete explicit input or an
already-derived surface report. Callers relying on word matching must supply
their own intent interpretation. Old serialized reports still round-trip;
this change does not rewrite existing notes or candidate queues.

`sdk.stats.regrounding_signals_for_surfaces(consumed_surface_refs=[...])`
resolves exact catalog names, catalog `surface_ref` values, or SDK-qualified
refs. The compatibility `regrounding_signals_for_intent` method ignores prose
for selection and requires `consumed_surface_refs` to return signals. Risk
and coverage requirements for explicitly consumed surfaces are unchanged.
