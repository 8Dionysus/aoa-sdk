# Plan Compilation Trials

This directory retains public-safe receipts for the C1-to-C2 integration
boundary. The executable source of each observation is the adjacent
`scripts/` verifier; receipts summarize exact inputs and outputs so a later
review can distinguish replayable evidence from a narrative claim.

`installed-wheel-golden-scenario-chain-v2.json` records two checks over one
isolated wheel:

- the legacy generated C2 fixture still reproduces its byte-exact golden plan;
- the public `AoASDK.control_plane` facade resolves, owner-binds, and compiles
  all three admitted live scenarios without fabricated contour participants.

The receipt proves deterministic control-plane construction against the named
pins. It does not activate a capability, execute a plan, establish task
benefit, measure cost reduction, prove consumer-zero, or authorize archive.

`fresh-context-full-chain-bounded-v1.json` retains the first no-history agent
that used only the published Python surface to resolve, bind, and compile a
bounded scenario. The behavior completed and independently replayed, but the
child serialized several nested observation fields incorrectly. The receipt
keeps those gaps explicit and records the parent replay separately; it is not
presented as a fully self-describing child trace.
