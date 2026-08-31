# AGENTS.md

## Applies to

`mechanics/release-support/`.

## Role

Route the shared release-support mechanic for changelog, release audit, CI
posture, build, publication helper, and Repo Validation support.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/release-support/README.md`, `mechanics/release-support/ROADMAP.md`, `mechanics/release-support/parts/AGENTS.md`, `mechanics/release-support/parts/release-audit-publish-helper/README.md`, `mechanics/release-support/parts/public-support-ci-posture/README.md`, `CHANGELOG.md`, `docs/RELEASING.md`, `docs/RELEASE_CI_POSTURE.md`, `scripts/release_check.py`, `src/aoa_sdk/release/`.

## Boundaries

- Stay on the control plane.
- Do not make release helper output a GitHub Release or package publication.
- Keep sibling release truth in sibling repositories.
- Keep changelog claims tied to validation evidence.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report release-facing surfaces changed and the exact validation gate that ran.
