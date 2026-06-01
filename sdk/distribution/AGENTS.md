# AGENTS.md

## Applies To

This card applies to `sdk/distribution/`.

## Role

`sdk/distribution/` names SDK package, release, and public support posture.

It routes distribution promises to package metadata, release-support
mechanics, CI posture, and release validation without pretending a dry run is a
published artifact.

## Read Before Editing

1. root `AGENTS.md`
2. `sdk/AGENTS.md`
3. `sdk/source_home.manifest.json`
4. `sdk/distribution/README.md`
5. the target family README
6. release-support mechanic cards
7. release docs and CI workflows when touched

## Boundaries

- Do not treat dry-run output as a GitHub Release or package upload.
- Do not broaden public support claims beyond tested surfaces.
- Keep package metadata, changelog, release docs, and release helpers aligned.
- Keep publication truth in GitHub tags/releases and package indexes.

## Validation

```bash
python scripts/validate_sdk_source_home.py
python scripts/release_check.py
python -m build
```

## Closeout

State whether package metadata, release posture, public support posture, CI, or
publication proof changed.
