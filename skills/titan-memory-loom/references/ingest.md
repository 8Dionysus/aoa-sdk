# Ingest mode

Create or update one local candidate index from a concrete Titan receipt
witness.

1. Require explicit Titan intent, receipt path and source ref, index path,
   source kind, bounded summary, and optional tags.
2. Inspect the receipt as a witness; do not infer that its named event actually
   occurred.
3. Initialize the index only when requested:

   `python <owner_root>/mechanics/titan/parts/memory-loom-recall-helper-contracts/scripts/titan_memory_loom.py init --workspace <workspace> --operator <operator> --out <index>`

4. Ingest the bounded receipt:

   `python <owner_root>/mechanics/titan/parts/memory-loom-recall-helper-contracts/scripts/titan_memory_loom.py ingest --index <index> --receipt <receipt> --source-kind <kind> --summary <summary> [--tags <tags>]`

5. Run `validate --index <index>`.
6. Return new record ids, receipt and source refs, candidate state, confidence
   posture, actual index write, validation, and `disposition: candidate_only`.

Do not promote the index into `aoa-memo` or owner truth.
