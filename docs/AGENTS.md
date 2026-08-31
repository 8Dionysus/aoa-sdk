# AGENTS.md

## Applies To

Root `docs/` surfaces, excluding stronger nested cards such as
`docs/decisions/AGENTS.md`.

## Role

Root docs are public route, boundary, versioning, workspace, design-reference,
and historical context surfaces.

`docs/README.md` is the docs entry map. Keep it route-oriented and weaker than
the source surface it points to.

## Relevant routes

The conditional references retained from this card are: `AGENTS.md`, `DESIGN.md`, `DESIGN.AGENTS.md`, `docs/README.md`, `mechanics/README.md`.

## Boundaries

- Keep part-specific operational docs under
  `mechanics/<parent>/parts/<part>/docs/`.
- Keep root release docs as thin route doors when a release-support part owns
  the detailed runbook or posture.
- Keep historical docs explicit as history; do not make seed notes active
  source truth.
- Route moved mechanic payload through its current part-local owner home.
- Do not preserve old root guidance or one-off impact prose in flat `docs/`
  when current owner surfaces already carry the route.

## Closeout

Report whether the edited doc is a root public route, a historical note, or a
mechanic-owned surface that should move into a part-local docs lane.
