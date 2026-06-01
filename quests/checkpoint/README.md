# Checkpoint Quest Lane

This lane is reserved for checkpoint and reviewed-closeout follow-through
records that need to survive the current diff.

Current SDK code may point future reviewed closeout follow-through to
`quests/checkpoint/captured/*.md`. The record itself should only be created
after a reviewed source event or owner handoff makes the obligation public-safe
and bounded.

Checkpoint mechanics own capture, review, and closeout validation. Questbook
owns source record placement and public obligation visibility.
