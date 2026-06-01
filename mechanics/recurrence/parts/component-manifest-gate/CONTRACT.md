# Component Manifest Gate Contract

## Owns

This part owns recurrence manifest discovery, tolerant classification, and scan
reports for SDK-readable recurrence manifest districts.

## Inputs

- `mechanics/recurrence/**/manifests/**/*.json`
- workspace-owner `manifests/recurrence/**/*.json`

## Outputs

- loaded `recurrence_component` entries
- known foreign manifest records
- explicit diagnostics for invalid, mixed, or adapter-required shapes

## Stop Lines

- no owner mutation
- no hidden adapter coercion
- no manifest shape laundering
- no projection authority
