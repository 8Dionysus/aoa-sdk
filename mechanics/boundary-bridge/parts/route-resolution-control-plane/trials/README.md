# Route Resolution Trials

This directory retains public-safe, bounded agent-in-the-loop observations for
C1. A child trace is an observation, not proof authority. Acceptance requires
an exact input artifact, a terminal return, and an independent parent replay
against the same installed package and routing snapshot.

`fresh-context-resolver-v2.json` records a paired lesson:

- T1-1 returned normally but was not accepted because it omitted the complete
  `RouteIntent`; its blocked result could not be distinguished from a strict
  compatibility constraint.
- T1-2 returned the full canonical input and digest. Parent replay reproduced
  the same decision ID, selected candidate, candidate count, snapshot digest,
  model equality, and byte equality.

Neither case invoked the selected capability or established task benefit.
