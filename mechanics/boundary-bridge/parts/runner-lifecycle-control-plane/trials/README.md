# Runner Lifecycle Trials

This directory retains reduced, public-safe T1 receipts for the public
`AoARunner` boundary. Raw child outputs remain session-local; each durable
receipt pins the exact request, wheel, typed input, parent validation, and
claim limit needed for later review.

`isolated-runtime-lifecycle-v1.json` records a fork-without-history subject
that exercised duplicate commands, sequential approvals, pause/resume,
disconnect, interruption, bounded recovery, a 64-progress-event lifecycle,
`SessionHandle` restore, outcome, and closeout through the deterministic
reference adapter. The adapter explicitly executes no plan steps, so this is
lifecycle evidence rather than production execution or task-benefit evidence.

`agent-os-g11-adversarial-corpus-v1.json` records a second
fork-without-history subject over 16 exact SDK cases, 5 exact runtime-owner
cases, and the incomplete-passport request/result schemas. It maps all 13
declared adversarial categories and 3 golden cases to their rightful terminal
boundaries. A blocked route is complete at its typed route stop; it is not
forced into a fabricated runtime chain.
