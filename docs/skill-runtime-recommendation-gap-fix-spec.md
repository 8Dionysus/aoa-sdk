# Skill Runtime Recommendation Gap Fix Spec

Recorded: `2026-04-06`
Status: `landed`
Owner repo: `aoa-sdk`

## Goal

Make `aoa skills enter`, `aoa skills guard`, `aoa skills detect`, and
`aoa skills dispatch` distinguish:

- recommendations the current host can act on directly
- recommendations that are semantically important but only router-visible to the
  current host
- recommendations whose host availability is still unknown

The landed path now keeps honest reporting and auto-discovers canonical install
roots so manual `--host-skill` input is an override surface rather than the
default way to get truthful availability.

## Why This Spec Exists

The current report shape can name a recommended skill without saying whether the
current host session can actually surface or invoke that skill directly.
That makes `must_confirm` and `suggest_next` look uniformly executable even when
some names are only visible in the router/control-plane layer.

See [skill-runtime-recommendation-gap.md](skill-runtime-recommendation-gap.md)
for the recorded operating problem and temporary fallback rule.

## Scope

This landed slice is limited to `aoa-sdk` control-plane reporting and canonical
install-root discovery:

- report models
- CLI and API inputs
- JSON payloads written by `enter` and `guard`
- test coverage for availability annotation

It does **not** try to solve:

- full Codex host installation or plugin sync beyond canonical install-root
  discovery
- canonical skill export ownership in `aoa-skills`
- automatic repair of missing host runtime skills
- a new enforcement regime that blocks all work whenever availability is
  unknown

## Non-Goals

- do not move skill meaning out of `aoa-skills`
- do not treat `router-only` as equivalent to `invalid`
- do not remove current `must_confirm` or `blocked_actions` semantics
- do not make `dispatch()` depend on external host inventory for its local
  activation behavior in this first slice

## Design Principles

1. Preserve the control-plane truth.
   A recommended skill can still be semantically correct even if the current
   host cannot expose it directly.

2. Separate recommendation truth from host actionability.
   The router answers "what matters next"; the host-availability layer answers
   "what can this session surface directly".

3. Stay backward-compatible by default.
   If no host inventory is supplied, the report should remain usable and mark
   availability as `unknown` rather than inventing false certainty.

4. Keep the first implementation slice bounded.
   The first landed improvement should annotate reports, not redesign the whole
   runtime path.

## Implemented Model Changes

Add one new model in `src/aoa_sdk/models.py`:

```python
class SkillHostAvailability(BaseModel):
    status: Literal["host-executable", "router-only", "unknown"]
    source: Literal[
        "host-manifest",
        "host-skill-list",
        "repo-install",
        "workspace-install",
        "user-install",
        "not-provided",
    ]
    manual_fallback_allowed: bool
    reason: str
```

Extend `SkillDispatchItem`:

```python
class SkillDispatchItem(BaseModel):
    skill_name: str
    layer: Literal["kernel", "outer-ring", "risk-ring"]
    collision_family: str | None = None
    reason: str
    host_availability: SkillHostAvailability
```

Extend `SkillDetectionReport`:

```python
class SkillDetectionReport(BaseModel):
    ...
    host_inventory_provided: bool = False
    actionability_gaps: list[str] = Field(default_factory=list)
```

### Status Meaning

- `host-executable`
  The current host inventory says the skill is directly available to this
  session.

- `router-only`
  The router recommends the skill, but the supplied host inventory says the
  current host cannot surface it directly. The skill still matters semantically,
  but the operator must use manual fallback or another route.

- `unknown`
  No host inventory signal was supplied, so the report cannot claim either
  direct availability or direct unavailability.

### `manual_fallback_allowed`

For this first slice:

- `true` for `must_confirm` and `suggest_next` items when `status` is
  `router-only`
- `false` for `activate_now` items, because `activate_now` should only describe
  actions the current route can perform directly

## Implemented Input Surface

Add optional host-availability input to the SDK APIs:

```python
SkillsAPI.detect(..., host_available_skills: list[str] | None = None)
SkillsAPI.dispatch(..., host_available_skills: list[str] | None = None)
```

Add matching optional detector-layer parameters:

```python
detect_skills(..., host_available_skills: list[str] | None = None)
dispatch_skills(..., host_available_skills: list[str] | None = None)
```

Add CLI options to `skills detect`, `skills dispatch`, `skills enter`, and
`skills guard`:

- repeated `--host-skill <skill-name>`
- optional `--host-skill-manifest <path>`

### Precedence Rule

For simplicity:

1. if `--host-skill` is supplied, use that list
2. else if `--host-skill-manifest` is supplied, load the list from the manifest
3. else auto-discover canonical install roots
4. else mark all item availability as `unknown`

The manifest format can stay minimal:

```json
{
  "skills": ["aoa-change-protocol", "aoa-adr-write"]
}
```

## Implemented Detection Behavior

### Without explicit host inventory

If canonical install roots are missing too, current routing behavior stays the
same, but every `SkillDispatchItem` gets:

```json
{
  "host_availability": {
    "status": "unknown",
    "source": "not-provided",
    "manual_fallback_allowed": false,
    "reason": "no host skill inventory was supplied"
  }
}
```

`host_inventory_provided` is `false`.
`actionability_gaps` stays empty because the report does not know enough yet.

### With host inventory

Annotate each recommendation:

- if `skill_name` is in the supplied host list:
  - `status = "host-executable"`
- else:
  - `status = "router-only"`

Then apply one extra rule:

- remove `activate_now` items that are not `host-executable`
- move them to `must_confirm` with a reason suffix such as
  `"strong tiny-router match ...; host inventory is router-only for this skill"`
- add the skill name to `actionability_gaps`

This keeps `activate_now` honest as a directly actionable lane.

### Auto-discovered install roots

When no explicit list or manifest is supplied, the detector now checks these
roots in order:

1. `<repo-root>/.agents/skills`
2. `<workspace-root>/.agents/skills`
3. `$HOME/.agents/skills`

The first populated root becomes the host inventory source with one of:

- `repo-install`
- `workspace-install`
- `user-install`

### `must_confirm` and `suggest_next`

Do not suppress semantically correct recommendations just because they are
`router-only`.
Instead:

- keep the item in its current lane
- annotate it as `router-only`
- set `manual_fallback_allowed = true`
- add it to `actionability_gaps`

## CLI Output

### Human-readable

Current output:

```text
must_confirm:
  - aoa-sanitized-share [risk-ring / safety-and-mutation-gating]
    reason: required explicit risk gate for mutation_surface=public-share
```

Proposed output:

```text
must_confirm:
  - aoa-sanitized-share [risk-ring / safety-and-mutation-gating / router-only]
    reason: required explicit risk gate for mutation_surface=public-share
    host: router-only via host-skill-list; manual fallback allowed
```

Add one summary line:

```text
actionability_gaps: aoa-sanitized-share, aoa-approval-gate-check
```

### JSON

Example item:

```json
{
  "skill_name": "aoa-sanitized-share",
  "layer": "risk-ring",
  "collision_family": "safety-and-mutation-gating",
  "reason": "required explicit risk gate for mutation_surface=public-share",
  "host_availability": {
    "status": "router-only",
    "source": "host-skill-list",
    "manual_fallback_allowed": true,
    "reason": "skill is not present in the supplied host inventory"
  }
}
```

Example report summary:

```json
{
  "host_inventory_provided": true,
  "actionability_gaps": [
    "aoa-sanitized-share",
    "aoa-approval-gate-check"
  ]
}
```

## Behavior Matrix

| Lane | Host status | Result |
|---|---|---|
| `activate_now` | `host-executable` | stay in `activate_now` |
| `activate_now` | `router-only` | demote to `must_confirm`, add to `actionability_gaps` |
| `activate_now` | `unknown` | keep current behavior in first slice, but annotate as `unknown` |
| `must_confirm` | `host-executable` | stay in `must_confirm` |
| `must_confirm` | `router-only` | stay in `must_confirm`, mark manual fallback |
| `must_confirm` | `unknown` | stay in `must_confirm`, annotate `unknown` |
| `suggest_next` | `host-executable` | stay in `suggest_next` |
| `suggest_next` | `router-only` | stay in `suggest_next`, mark manual fallback |
| `suggest_next` | `unknown` | stay in `suggest_next`, annotate `unknown` |

## Test Plan

Add or extend `aoa-sdk` tests to cover:

1. model serialization
   - `SkillDispatchItem` round-trips with `host_availability`
   - `SkillDetectionReport` round-trips with `host_inventory_provided` and
     `actionability_gaps`

2. detector behavior without any install root or explicit host inventory
   - existing routing result stays stable
   - all items report `status = "unknown"`

3. detector behavior with host inventory
   - matching skills become `host-executable`
   - missing `activate_now` skills are demoted out of `activate_now`
   - missing `must_confirm` skills remain present but marked `router-only`

4. CLI JSON behavior
   - default auto-discovery from install roots
   - `skills detect --json --host-skill aoa-change-protocol`
   - `skills guard --json --host-skill aoa-change-protocol`
   - `skills enter --json --host-skill-manifest ...`

5. persisted report files
   - `enter` and `guard` report payloads keep the new fields when written to
     `.aoa/skill-dispatch/*.json`

## Follow-On

Possible later tightening:

After host inventory becomes reliable, consider stronger rules such as:

- warning or soft-fail when `must_confirm` is entirely `router-only`
- explicit report verdicts for "manual fallback required"
The landed fix removes the default dependency on manual `--host-skill` lists,
but it does not add those stricter enforcement hooks yet.

## Open Questions

1. Should `dispatch()` ever refuse to auto-activate when host availability is
   `unknown`, or should that remain purely a reporting concern?
2. Should the host manifest carry only names, or also handles and source refs?
3. Should `router-only` items produce a new report-level warning field in
   addition to `actionability_gaps`, or is the gap list sufficient?

## Outcome

This fix now covers:

- model additions
- detector annotation
- canonical install-root auto-discovery
- CLI option plumbing and explicit override precedence
- persisted JSON parity
- tests

That is enough to eliminate the default "recommended but not clearly available"
ambiguity without pretending that full host packaging and sync is solved.
