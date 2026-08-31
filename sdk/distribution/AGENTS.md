# AGENTS.md

## Applies To

This card applies to `sdk/distribution/`.

## Role

`sdk/distribution/` names SDK package, release, and public support posture.

It routes distribution promises to package metadata, release-support
mechanics, CI posture, and release validation without pretending a dry run is a
published artifact.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `AGENTS.md`, `sdk/AGENTS.md`, `sdk/source_home.manifest.json`, `sdk/distribution/README.md`.

## Boundaries

- Do not treat dry-run output as a GitHub Release or package upload.
- Do not broaden public support claims beyond tested surfaces.
- Keep package metadata, changelog, release docs, and release helpers aligned.
- Keep publication truth in GitHub tags/releases and package indexes.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

State whether package metadata, release posture, public support posture, CI, or
publication proof changed.
