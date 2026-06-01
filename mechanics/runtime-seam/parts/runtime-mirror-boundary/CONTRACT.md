# Runtime Mirror Boundary Contract

## Guarantees

- Reports source checkout preference explicitly.
- Treats missing future surfaces as missing, not as compatible.
- Keeps live compatibility checks separate from generated fixture parity.

## Non-Goals

- It does not provision runtime mirrors.
- It does not patch sibling repos to satisfy SDK checks.
- It surfaces incompatible paths as missing or incompatible.
