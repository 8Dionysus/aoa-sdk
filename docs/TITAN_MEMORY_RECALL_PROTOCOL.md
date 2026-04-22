# Titan Memory Recall Protocol

## Required recall fields

- record id
- source kind
- source ref when available
- session id when available
- titan and lane
- authority note
- confidence
- status

## Verification path

1. Read recall result.
2. Open source ref or owner-repo artifact.
3. Check wave manifest or source seed if a seed claim is involved.
4. Ask Sentinel to flag drift risk.
5. Only then ask Delta for verdict if judgment is needed.
