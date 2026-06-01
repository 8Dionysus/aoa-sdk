# AoA Experience Capture Pipeline Helper

This part plants only a thin control-plane helper route for the three seed zips:

- `/home/dionysus/Загрузки/aoa-experience-mechanic-seed-v0_1.zip`
- `/home/dionysus/Загрузки/aoa-experience-runtime-capture-seed-v0_2.zip`
- `/home/dionysus/Загрузки/aoa-experience-pilot-integration-seed-v0_3.zip`

This note is for `aoa-sdk` helper API shape only.

## Boundary

- `aoa-sdk` may describe, load, and validate capture/pipeline helper candidates
- `aoa-sdk` does not own experience law, worker services, runtime activation, certification, deployment, or governance
- the seam stays requested-only and helper-only
- generated transport noise, cache spill, and runtime mirror chatter stay out of this surface

## Helper shape

The helper seam is intentionally small:

- capture helper: normalize seed-zip ingress into reviewable helper inputs
- pipeline helper: order the capture -> validate -> stage -> review path as a candidate API
- pilot record shape: keep the output pointed at reviewable pilot records, not at live execution

## What This Helper Does Not Do

- no worker service launch
- no runtime activation
- no certification path
- no deployment path
- no governance rewrite

## Companion contract files

- schema: `schemas/capture-pipeline-helper.schema.json`
- example: `examples/capture-pipeline-helper.example.json`
