# Check Document Contracts, Not Editorial Snapshots

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0109
- Original date: 2026-09-21
- Surface classes: validation guard, documentation, agent guidance
- SDK facets: validation, control-plane, agent surface
- Mechanic parents: release-support
- Guard families: agent mesh, owner authority, route integrity
- Posture: accepted

## Context

Documentation checks accumulated exact sentences, unconsumed heading names,
and reconciliation numbers from one historical release. Safe rewording could
fail while an instruction containing the required phrase inside its negation
could pass. README-reading heuristics also treated incidental words as evidence
of a conditional route. These checks did not establish the semantic authority
suggested by their names.

The route and owner laws in AOA-SDK-D-0105 remain useful. The missing distinction
is between mechanically checkable document contracts and source-aware review of
guidance meaning. This distinction must survive later additions to the suite;
a commit describing a one-off test cleanup would not preserve that boundary.

## Options Considered

- Preserve and expand the phrase inventories and conditional-reading regexes.
- Remove documentation checks together with their real structural guarantees.
- Retain concrete route, coverage, and command-placement checks; return semantic
  judgments and editorial policy to source-aware review.

## Decision

Choose the third option for root docs/route tests and the nested-agent validator.
Required agent-card paths, root executable-route references, actual navigation
destinations, and recognized command placement remain machine checks. Public
license identity remains bound to project metadata and the license source.

Retire mandatory prose snippets, duplicate-paragraph fingerprints, unconsumed
heading names, and the heuristic verdict on conditional README reading.
Retire the ordinary test snapshot of version 0.5.0's historical counters.
The narrow Unreleased counter lint remains an explicitly editorial policy check,
not validation of release facts. Do not replace removed assertions with a new
semantic phrase vocabulary or an assertion registry.

Guidance review still checks owner boundaries, contradictions with stronger
sources, task-conditional reading, and unnecessary inherited repetition. The
review route is explicit in DESIGN.AGENTS.md and VALIDATION.md. This decision
narrows the automatic checker claim; it does not relax those source laws.

Tests for a checker must reject independently specified bad inputs and admit
safe changes. Current-tree validation remains distinct from checker regression
testing. Product tests continue to own passive inspection, reviewed handoff,
no-execution, identity, and other behavioral guarantees. Prose tests neither
provided nor replace that behavioral coverage.

## Rationale

A durable test needs a persistent failure risk and a useful oracle. Merely
being unique, or catching an editorial difference, does not establish either.
Documentation is important agent input, but substring matching cannot certify
its meaning. Explicitly bounded automated claims and source-aware review make
the remaining confidence honest while permitting ordinary maintenance.

## Consequences

- Safe wording and link-label changes no longer require synchronized snapshots.
- Missing cards, wrong route destinations, and recognized misplaced commands
  still fail mechanically.
- Guidance meaning and instruction-level contradictions require real review;
  no automatic semantic-proof or model-behavior claim is made.
- Existing SDK behavior, full release/CI gates, and their blocking posture are
  unchanged. This is not a measured whole-suite or landing-speed claim.
- Other owner surfaces and validators are not mechanically converted by analogy.

## Source Surfaces

- `scripts/validate_nested_agents.py`
- `tests/test_validate_nested_agents.py`
- `tests/test_docs_routes.py`
- `tests/test_design_surfaces.py`
- `DESIGN.AGENTS.md`
- `VALIDATION.md`
- `docs/decisions/AOA-SDK-D-0105-prompt-light-agent-routes-and-on-demand-validation.md`

## Follow-Up Route

Apply the same risk and safe-change questions when modifying these checks.
Keep any newly identified product-behavior gap with its actual product owner;
do not claim it closed by restoring a mandatory sentence.

## Verification

Use the docs/route and nested-agent tests, the nested-agent validator, decision
index parity, and the full owner gate through root VALIDATION.md. Exercise
safe rewording and concrete broken routes/command drift separately, and inspect
the retained product-boundary tests during review.
