# Experience Capture Pipeline Helper

## Role

This part owns the SDK-local capture/pipeline helper contract for Experience
seed intake.

## Input

- `docs/capture-pipeline-helper.md`
- `schemas/capture-pipeline-helper.schema.json`
- `examples/capture-pipeline-helper.example.json`

## Output

- a validated helper-shape example for reviewable capture, validate, stage,
  and review flow

## Owner

`aoa-sdk` owns the schema, public-safe example, doc boundary, and regression
test. Experience owners retain capture law, worker services, runtime
activation, certification, deployment, and governance.

## Start Here

- [CONTRACT](CONTRACT.md)
- [VALIDATION](VALIDATION.md)
- [docs](docs/)

## Artifact Homes

- `docs/` - active helper boundary
- `examples/` - public-safe helper example
- `schemas/` - helper contract
- `tests/` - part-local regression check

## Next Route

Use `../../PROVENANCE.md` for former root-path accounting and
`../../../topology.json` for repo-wide route law.
