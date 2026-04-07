# Skill Runtime Recommendation Gap

Recorded: `2026-04-06`
Status: `resolved in aoa-sdk control-plane reporting`

## Context

`aoa-sdk` owns the workspace-facing control-plane path for `aoa skills enter`,
`aoa skills guard`, `aoa skills detect`, and `aoa skills dispatch`.
Those surfaces can return `activate_now`, `must_confirm`, `suggest_next`, and
`blocked_actions` based on the current repo, phase, and mutation surface.

During a real cross-repo remediation session, the `enter` and `guard` reports
recommended several skills that were meaningful for the route, including
`aoa-approval-gate-check`, `aoa-dry-run-first`, `aoa-sanitized-share`,
`aoa-session-donor-harvest`, and related session-growth skills.

In the same session, the host-visible Codex skill inventory did not expose all
of those recommended skills as directly readable `SKILL.md` bodies.
That created a tooling gap:

- the router output was real and should not be ignored
- the session could not honestly claim direct execution of every recommended
  skill
- public-share and mutation gating still needed a bounded operating rule

## Problem

When a control-plane report recommends a skill that is not available in the
current host skill inventory, the operator faces three bad outcomes:

1. ignore the router output and continue as if nothing happened
2. pretend the missing skill was used directly
3. stop all work even when the route can still proceed safely with explicit
   fallback discipline

The first two outcomes are unsafe or dishonest.
The third outcome is sometimes too brittle for bounded reviewed work, especially
when the report is signaling a real risk gate rather than a nice-to-have hint.

## Options Considered

### 1. Ignore unavailable recommendations

Reject this.
It would make `must_confirm` and `blocked_actions` informational theater.

### 2. Claim the unavailable skill was used indirectly

Reject this.
It would blur the difference between a real skill invocation and a manual
approximation.

### 3. Use an explicit manual-equivalence fallback while recording the gap

Choose this for now.
If a recommended skill is unavailable in the current host inventory, the
operator may proceed only when the route still respects the same bounded safety
contract in visible form.

## Decision

`aoa-sdk` now auto-discovers host inventory from canonical install roots before
falling back to `unknown`:

- `<repo-root>/.agents/skills`
- `<workspace-root>/.agents/skills`
- `$HOME/.agents/skills`

When none of those roots is populated and no explicit host inventory is
supplied, use this fallback rule:

- treat `must_confirm` and `blocked_actions` from `enter` and `guard` as real
  control-plane signals even when the named skill is not directly available in
  the session inventory
- do not claim that an unavailable skill was used
- if the work continues, state that the route is following a manual fallback
  that preserves the same discipline in visible form
- for `public-share` or other gated mutation, require explicit user confirmation
  and keep sanitization or dry-run posture manual, narrow, and reviewable
- if the same discipline cannot be preserved manually, stop rather than
  continuing on router theater

## Consequences

- reviewed work can continue without pretending that unavailable skills ran
- router outputs remain actionable instead of decorative
- public-share and mutation work still require explicit confirmation and bounded
  sanitization posture
- the old hidden gap is now downgraded into an explicit fallback case when no
  install root is present

The preferred steady-state shape is that recommended skills are either:

- directly available in the host inventory, or
- explicitly marked as unavailable-to-host so the report does not look directly
  executable when it is not

## Follow-Up

The landed fix now covers the first honest end-to-end step:

1. auto-discover canonical install roots before defaulting to `unknown`
2. distinguish executable recommendations from router-only recommendations in
   the report surface
3. keep a control-plane test that fails when host availability is mislabeled

Possible next tightening, if needed later:

1. expose the discovered install root more explicitly in a first-class report
   field instead of only through availability source and reasoning lines
2. add an optional strict mode that fails fast when required risk-gate skills
   are router-only

The concrete first-slice design now lives in
[skill-runtime-recommendation-gap-fix-spec.md](skill-runtime-recommendation-gap-fix-spec.md).

## Why This Belongs Here

This note belongs in `aoa-sdk` because the gap appears at the control-plane seam
owned by the SDK:

- `aoa-sdk` emits the recommendation and gating reports
- `aoa-skills` remains the owner of canonical skill meaning and export surfaces
- the host session inventory is downstream from both and should not silently
  rewrite either layer's meaning

The note records the current operating rule without moving skill meaning out of
`aoa-skills` and without treating one session fallback as permanent doctrine.
