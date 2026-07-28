# Unified Evidence and Closeout Chain

This part owns the SDK projection that reconnects one Agent OS run after the
runtime outcome without changing proof, memory, checkpoint, or closeout
authority.

`EvidenceChain` embeds the immutable SDK control-plane objects needed to audit
the route and execution. Runtime evidence remains a runtime-owned ref.
Eval verdicts, memory receipts, checkpoint receipts, and the final closeout
bundle remain owner-qualified refs; their canonical payloads are never copied
into the SDK projection.

`EvidenceChainRepository` records immutable partial and complete revisions
under one explicit absolute root. Its checked index resolves the current chain
by exact `SessionHandle` identity or final closeout receipt ID without scanning
workspaces or guessing owner paths.

See [CONTRACT](CONTRACT.md) and [VALIDATION](VALIDATION.md).
