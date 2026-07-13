# Recurrence Beacon Candidate CLI Route

This route covers the recurrence flow from an owner signal through bounded
observations, beacon candidates, the candidate ledger, and usage-gap readout.

The executable command family is owned by the recurrence CLI under
`src/aoa_sdk/recurrence/`; focused checks and fixtures are owned by the part
`VALIDATION.md` and part-local tests.

## Practical rule

Start with one real signal source and one manual supplemental packet.
Candidate packets remain weaker than their owner sources and review route.
