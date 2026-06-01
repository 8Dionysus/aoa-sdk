# Control Plane Capsule Contract

## Guarantees

- Publishes only low-context routing refs, not implementation internals.
- Fails validation when generated output diverges from the canonical builder.
- Keeps validation refs explicit and resolvable.

## Non-Goals

- It does not replace design docs, decisions, or mechanics contracts.
- It does not load sibling data or make compatibility decisions by itself.
