# Recall mode

Recall bounded local candidates without replacing source verification.

1. Require explicit Titan intent, concrete index, bounded query, optional Titan
   or tag filter, and result limit.
2. Validate the index before recall.
3. Run:

   `python <owner_root>/mechanics/titan/parts/memory-loom-recall-helper-contracts/scripts/titan_memory_loom.py recall --index <index> --query <query> [--titan <name>] [--tag <tag>] [--limit <n>]`

4. Preserve record id, source refs, confidence, state, redaction posture, and
   authority warning for every hit.
5. Separate candidate, confirmed-by-source, masked, and tombstoned states. The
   helper itself does not establish `confirmed-by-source`.
6. Return `actual_effects: []`, uncertainty, and the exact source or memo route
   required before using a material claim.

No hit is not proof that the source event never happened.
