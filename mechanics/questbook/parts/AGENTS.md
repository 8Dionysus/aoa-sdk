# AGENTS.md

## Applies to

This card applies to `mechanics/questbook/parts/`.

## Role

Questbook parts keep root quest source records, the public index, lifecycle
posture, and future dispatch readers structurally separate.

Stay on the control plane. Part edits here change route law; they do not
complete quest work or activate helper payload.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.
