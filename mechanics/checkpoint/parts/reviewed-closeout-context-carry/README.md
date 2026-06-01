# Reviewed Closeout Context Carry

This part owns the SDK route from reviewed checkpoint/closeout reread to
advisory carry packets.

## Role

Input: reviewed closeout context, checkpoint lineage hints, surviving owner
followthrough candidates, component-refresh hints, continuity anchors, and
next-kernel route pressure.

Output: schema-checked advisory maps and decisions that can be inspected by
owner layers without minting owner truth.

Owner: `aoa-sdk` owns the carry packet shapes, examples, and validation.
Owner repositories decide candidate identity, seed staging, object identity,
component refresh, continuity truth, progression, proof, memory, and execution.

## Active Surfaces

- [Candidate Lineage Carry](docs/candidate-lineage-carry.md)
- [Owner Followthrough Map](docs/owner-followthrough-map.md)
- [Component Refresh Followthrough](docs/component-refresh-followthrough.md)
- [Self-Agency Continuity Carry](docs/self-agency-continuity-carry.md)
- [Next-Kernel Followthrough Decision](docs/next-kernel-followthrough-decision.md)
- [Schemas](schemas/)
- [Examples](examples/)
- [Context Carry Tests](tests/test_reviewed_closeout_context_carry.py)
- [Component Refresh Tests](tests/test_component_refresh_followthrough.py)

## Next Route

Route owner landing to owner repositories, proof to `aoa-evals`, durable memory
to `aoa-memo`, progression to the progression owner, and execution to the
explicitly invoked skill or runtime owner.
