# Operator Console Helper Contracts Contract

## Contract

The part validates SDK-visible Titan console helper state without becoming the
operator authority.

## SDK-Owned Active Names

- part route: `titan/operator-console-helper-contracts`
- docs: `docs/operator-console.md`
- script: `scripts/titan_console.py`
- schemas: console state, console event, and operator approval schemas
- examples: console state and event-stream examples
- tests: `tests/test_titan_console.py`

## Stop-Lines

- Do not treat console state validity as live operator approval.
- New console states must identify themselves as witness-only helper
  projections with runtime not run, transport not sent, and unauthenticated
  operator attribution.
- Ungated roster entries begin declared and gated entries begin locked; helper
  `active` never means live runtime activation.
- Approval writes require and preserve an external decision reference plus
  approver attribution while explicitly remaining unauthenticated
  witness-only data.
- Do not widen appserver-plan output into Codex projection authority.
- Do not synthesize summon intent or pin a model when the caller did not
  provide them; appserver-plan requires a bounded prompt and leaves an
  unspecified model to the runtime owner.
- Do not keep console helper artifacts in root technical districts.
