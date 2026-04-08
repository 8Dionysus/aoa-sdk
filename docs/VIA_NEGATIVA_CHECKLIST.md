# VIA_NEGATIVA_CHECKLIST

This checklist is for `aoa-sdk` as the typed control-plane helper seams.

## Keep intact

- helpers that narrow ergonomics without stealing policy
- typed fixtures and interfaces that expose posture explicitly
- compatibility checks and narrow dispatch seams

## Merge, move, suppress, quarantine, deprecate, or remove when found

- wrappers that hide routing, fallback, or mutation policy
- overlapping helper surfaces for the same owner operation
- fixtures that encode obsolete or shadow policy

## Questions before adding anything new

1. Does this helper clarify ownership, or hide it?
2. Can caller-supplied posture replace baked-in behavior?
3. Is there already a narrower helper for this seam?

## Safe exceptions

- migration shims with expiry and clear warnings
- new typed seams where the ownership boundary remains explicit

## Exit condition

- SDK should feel like a scalpel, not a puppet theater.
