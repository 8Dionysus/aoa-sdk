# Titan Swarm Ledger

The Titan swarm ledger records task contracts, reports, findings, grades,
timeouts and closeout memory candidates.

It is local-first and does not spawn agents. It is a visible trace surface
that lets future sessions audit what the Titan cohort actually contributed.

## Why this exists

Field sessions showed that agent work can materially improve a campaign but
then disappear into chat context. The swarm ledger makes that participation
durable without promoting it into truth.

## Lifecycle

```text
start ledger
  -> assign task
    -> receive report
      -> update finding lifecycle
        -> grade participation
          -> closeout audit
            -> memory candidates
```

## Key boundary

A Titan report is not memory.  
A memory candidate is not owner truth.
