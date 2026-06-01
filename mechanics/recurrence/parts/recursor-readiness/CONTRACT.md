# Recursor Readiness Contract

## Owns

This part owns SDK read-only recursor readiness scanning.

## Inputs

- `aoa-agents` recursor role contracts
- pair separation config
- projection candidate config

## Outputs

- readiness projection
- boundary scan report
- projection candidate report

## Stop Lines

- no agent spawn
- no default install
- no arena session
- no verdict, scar, rank, or hidden scheduler action
