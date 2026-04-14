# Connectivity Doctor

The doctor exists to expose thin seams before they become folklore.

## What it checks

- generated surfaces with no named source inputs
- projected surfaces with no named generated seam
- generated surfaces with no proof command
- components with no explicit refresh route
- unresolved `component:` edges
- owner handoffs that point into repos with no planted recurrence manifests
- downstream route edges that still lack route commands
- changed paths that match no planted component

## Why this matters

The first real landing of recurrence will reveal where the project is still under-connected.

That is not a failure. That is part of the point.

## Reading the output

Not every gap is equally urgent.

Use rough severity this way:

- high: recurrence cannot honestly explain provenance
- medium: recurrence can see the seam but cannot plan it cleanly
- low: the seam is named, but the downstream repo still needs its own planted manifest
