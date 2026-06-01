# Decision Records Index

This directory is the durable decision surface for `aoa-sdk`.

Use it when a future contributor needs the rationale for a route, topology,
owner split, validator route, workflow boundary, compatibility posture,
control-plane API boundary, or SDK source/mechanic split.

Ordinary implementation notes, generated output, runtime logs, private
evidence, proof verdicts, memory objects, and one-off planning thoughts route
to their owning surfaces instead.

## Operating Card

| Field | Route |
| --- | --- |
| role | durable decision rationale entrypoint and index chooser |
| input | changed SDK source surface, owner boundary, rejected option, validation guard, or cross-surface route pressure |
| output | canonical decision note, generated lookup indexes, and route back to the source surface |
| owner | `docs/decisions/AGENTS.md` for lane law; decision notes for rationale; generated indexes for lookup only |
| next route | source surface first, then nearest route card, `docs/boundaries.md`, `ROADMAP.md`, generated lookup indexes, or the affected sibling owner |
| validation | `python scripts/generate_decision_indexes.py --check` plus the owning validator for the changed surface |

## Authority

Decision notes explain why a route was chosen.

They are weaker than the source surface they describe:

- SDK source and importable API meaning stay in `src/aoa_sdk/`;
- root route law stays in `AGENTS.md`;
- owner boundaries stay in `docs/boundaries.md`;
- direction stays in `ROADMAP.md`;
- generated companions stay derived from builders and source surfaces;
- sibling repositories keep their stronger truth for skills, techniques,
  evals, memo, agents, routing, playbooks, stats, KAG, and runtime behavior.

Generated decision indexes are weaker than the decision notes. They exist to
make lookup cheaper for agents, not to carry decision rationale.

## Index Shape

Each decision owns:

- a canonical `Decision ID: AOA-SDK-D-####`;
- a full canonical-ID filename, for example `AOA-SDK-D-0001-*.md`;
- an `## Index Metadata` block naming original date, surface classes, SDK
  facets, mechanic parents, guard families, and posture.

The lookup indexes under [indexes](indexes/README.md) are generated from that
metadata:

- [Decisions by canonical ID and number](indexes/by-number.md)
- [Decisions by date](indexes/by-date.md)
- [Decisions by surface class](indexes/by-surface.md)
- [Decisions by SDK facet](indexes/by-sdk-facet.md)
- [Decisions by mechanic parent](indexes/by-mechanic.md)
- [Decisions by validation or guard family](indexes/by-guard.md)

Regenerate the read models after decision metadata changes:

```bash
python scripts/generate_decision_indexes.py
```

Check generated parity before closeout:

```bash
python scripts/generate_decision_indexes.py --check
```

## Active Mechanics Decision

The corrected parent mechanics topology is recorded in
`AOA-SDK-D-0005-mechanics-parent-boundary-correction.md`. The source-family
coverage guard is recorded in
`AOA-SDK-D-0006-mechanics-source-family-crosswalk.md`. The first
mechanic-owned payload localization is recorded in
`AOA-SDK-D-0007-mechanic-artifact-localization.md`. Codex Projection artifact
localization is recorded in
`AOA-SDK-D-0008-codex-projection-artifact-localization.md`. Agon and
Experience part-local helper localization is recorded in
`AOA-SDK-D-0009-agon-experience-part-localization.md`. The remaining
Experience helper contract bundles are localized in
`AOA-SDK-D-0010-experience-helper-contract-part-localization.md`. Titan helper
contract bundles are localized in
`AOA-SDK-D-0011-titan-helper-contract-part-localization.md`. Recurrence
control-plane payload is localized in
`AOA-SDK-D-0012-recurrence-control-plane-part-localization.md`. Boundary Bridge
and Checkpoint active payload is localized in
`AOA-SDK-D-0013-boundary-checkpoint-active-part-localization.md`.
Antifragility stress-posture dispatch, reviewed stress closeout carry, and via
negativa pruning payload is localized in
`AOA-SDK-D-0014-antifragility-active-part-localization.md`. RPG typed consumer
API and surface-path transport payload is localized in
`AOA-SDK-D-0015-rpg-typed-consumer-part-localization.md`. Checkpoint reviewed
closeout context carry payload is localized in
`AOA-SDK-D-0016-checkpoint-closeout-context-carry-localization.md`. Boundary
Bridge skill-runtime bridge payload is localized in
`AOA-SDK-D-0017-skill-runtime-bridge-part-localization.md`. Release Support
runbook, public support posture, and release helper tests are localized in
`AOA-SDK-D-0018-release-support-part-localization.md`. Codex Projection
workspace MCP server docs, runnable script, and tests are localized in
`AOA-SDK-D-0019-codex-workspace-mcp-server-localization.md`. Technique
publication hook guidance is localized as a recurrence observation boundary in
`AOA-SDK-D-0020-technique-publication-observation-boundary-localization.md`.
The `aoa-techniques` promotion-readiness facade regression is localized in
`AOA-SDK-D-0021-technique-promotion-readiness-reader-localization.md`.
Reviewed session handoff runner docs and operator scripts are localized in
`AOA-SDK-D-0022-reviewed-session-handoff-runner-localization.md`.
Session-growth checkpoint cycle docs are localized in
`AOA-SDK-D-0023-session-growth-checkpoint-cycle-localization.md`. Active
mechanics topology status naming is recorded in
`AOA-SDK-D-0034-active-mechanics-topology-status-naming.md`. Diagnostic catalog
compatibility path canonicalization is recorded in
`AOA-SDK-D-0035-diagnostic-catalog-compatibility-path-canonicalization.md`.
Root technical district allowlist validation is recorded in
`AOA-SDK-D-0036-root-technical-district-allowlist-validation.md`. Workspace
MCP surface-crosswalk naming is recorded in
`AOA-SDK-D-0037-workspace-mcp-surface-crosswalk-secondary-route-naming.md`.
Skill and surface manual-equivalence naming is recorded in
`AOA-SDK-D-0038-manual-equivalence-active-lane-naming.md`. A2A quest-passport
secondary-tier naming is recorded in
`AOA-SDK-D-0039-a2a-quest-passport-secondary-tier-naming.md`. Sibling
fallback-key input alias normalization is recorded in
`AOA-SDK-D-0040-sibling-fallback-field-input-alias-normalization.md`.
External stress fallback-ref accounting is recorded in
`AOA-SDK-D-0041-external-stress-fallback-ref-accounting.md`. Questbook source
store restoration is recorded in
`AOA-SDK-D-0042-questbook-source-store-restoration.md`. The checked SDK
source-home tree is recorded in
`AOA-SDK-D-0043-sdk-source-home-tree.md`.

Together they supersede the first inventory-based skeleton's parent package set
and replace the old route-only posture with a controlled part-local payload
rule: single-mechanic artifacts move into functioning parts, while root keeps
only public, shared, repo-wide, tooling-facing contracts, or the Questbook
source-record district.

## Addressing

Full canonical-ID decision paths are the active source files:

- `docs/decisions/AOA-SDK-D-0001-*.md`
- `docs/decisions/AOA-SDK-D-0002-*.md`
- `docs/decisions/AOA-SDK-D-####-*.md`

Canonical IDs remain stable handles. Previous path names belong to git, PR, or
release history, not to a compatibility lookup layer.

## Naming

Use the full canonical decision ID as the filename prefix:

`AOA-SDK-D-0001-short-decision-slug.md`

Prefer short titles that name the route, not the whole debate.

## Template

Start from [TEMPLATE.md](TEMPLATE.md) for new decisions. Keep notes concise,
but include enough context, options, rationale, consequences, source surfaces,
and validation for a future agent to avoid repeating the same route question.
