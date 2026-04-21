# Recursor No-Spawn Law

This recurrence wave prepares future recursor agents but does not run them.

Forbidden command surface:

```text
aoa recur agents spawn
aoa recur agents run
aoa recur agents summon
aoa recur agents open-arena
```

Any future command that resembles these verbs must fail owner review unless a
later explicit agent/runtime wave authorizes it.

The current SDK seam is read-only:

```text
readiness
boundary-check
projection-candidates
```
