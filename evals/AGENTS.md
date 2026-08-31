# AGENTS.md

## Applies to

This card applies to `aoa-sdk/evals/` and every file below it.

## Role

This skeleton port captures SDK-layer eval pressure before it is accepted,
rejected, or normalized by `aoa-evals`.

`aoa-evals` owns central verdict, scoring, regression, and proof doctrine
authority. This port owns only SDK-local intake, cases, fixtures, suites,
reports, and source refs.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `AGENTS.md`, `README.md`, `PORT.yaml`, `aoa-evals`.

For central proof adoption questions, consult the local eval-port standard in aoa-evals only when that central route is active.

## Boundaries

- Keep typed helper behavior, compatibility posture, workspace discovery,
  control-plane boundaries, and additive surface detection in `aoa-sdk`.
- Keep proof doctrine, verdicts, scoring, and regression authority in
  `aoa-evals`.
- Do not treat an intake packet as proof acceptance or a central eval verdict.
- Do not place private traces, secrets, or unreduced operator evidence here.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report changed eval surfaces, current `PORT.yaml` status, validation run, any
skipped central proof adoption, and the next route into `aoa-evals` when needed.
