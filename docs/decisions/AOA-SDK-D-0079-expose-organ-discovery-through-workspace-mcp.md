# Expose Organ Discovery Through Workspace MCP

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0079
- Original date: 2026-07-26
- Surface classes: MCP projection, organ discovery, progressive disclosure
- SDK facets: control-plane, workspace discovery, MCP projection
- Mechanic parents: codex-projection, boundary-bridge
- Guard families: deny-by-default admission, owner boundary, bounded context, no execution
- Posture: accepted source candidate

## Context

`AOA-SDK-D-0075` established the typed organ registry, progressive discovery
API, compatibility checks, and candidate activation-plan compiler. The Python
API and CLI could inspect that registry, but the existing workspace MCP exposed
only general workspace orientation. An agent could therefore see that an organ
route existed without using the SDK-owned `catalog -> organ -> capability`
sequence through its normal workspace access plane.

Adding the full control plane to MCP would collapse discovery, authorization,
and execution into one ambient surface. Leaving discovery CLI-only would keep a
second, avoidable access path and encourage static always-loaded organ catalogs.

The same Wave 6 owner review also found that the workspace map still advertised
the retired Dionysus repo-local MCP launcher even though the current owner
defines a privacy-bounded interview and portrait protocol and defers MCP
integration.

## Options Considered

- Keep organ discovery available only through Python and CLI.
- Expose discovery, activation-plan compilation, connection, and execution
  through one workspace MCP surface.
- Project only registry status and progressive discovery through the existing
  workspace MCP, while keeping candidate compilation and all runtime effects on
  their stronger owner routes.

## Decision

Choose the third option.

The existing `aoa_workspace` server exposes four additional tools:

- `organ_registry_status`;
- `organ_catalog`;
- `organ_inspect`;
- `organ_capability`.

It also exposes static status and catalog resources plus URI templates for one
organ and one capability. Catalog reads retain the SDK result and byte bounds
and do not preload primitive schemas. All eleven workspace tools carry
read-only, non-destructive, idempotent, closed-world annotation hints.
Annotations are descriptive only and never grant policy, admission, or
authorization.

The MCP surface deliberately omits activation-plan compilation, registry
mutation, credential resolution, connection, lifecycle, owner-tool proxying,
and execution. Candidate compilation remains an explicit SDK/CLI/host action;
runtime execution remains with the host and `abyss-stack`. The server reads
only an exact registry configured through the workspace manifest or
`AOA_SDK_ORGAN_REGISTRY`; it does not infer admission from repository,
process, endpoint, or consumer scans.

The workspace map replaces the stale Dionysus MCP launcher with the current
owner-authored interview catalog and privacy stop-line.

## Rationale

Progressive discovery is the smallest useful MCP projection of the control
plane. It lets an agent learn only the organ and capability needed for the
current task without making the workspace server a mega-gateway or confused
deputy. Keeping plan compilation off MCP creates an explicit boundary between
inspection and any future authorization step.

## Consequences

- Agents can discover typed organ access through their existing workspace MCP.
- Consumers still need an explicit private registry; an empty or invalid
  configuration fails closed.
- A visible resource, annotation, endpoint, or successful discovery call does
  not prove admission, maturity, owner acceptance, or benefit.
- Host integration must deliberately cross from MCP discovery to SDK plan
  compilation and then to runtime execution.
- Dionysus is no longer presented as an active MCP provider.

## Source Surfaces

- `docs/decisions/AOA-SDK-D-0075-owner-bounded-organ-access-control-plane.md`
- `src/aoa_sdk/codex/workspace_mcp.py`
- `src/aoa_sdk/organs/`
- `mechanics/codex-projection/parts/workspace-mcp-server/`
- `mechanics/boundary-bridge/parts/organ-access-control-plane/`

## Follow-Up Route

Keep OS-private registry instances and consumer projections outside the SDK
package. Route runtime connection, lifecycle, and effect execution to
`abyss-stack`; route proof to `aoa-evals`; require each organ owner to retain
payload meaning and acceptance.

## Verification

Run the workspace MCP focused tests, organ-access contract and schema checks,
decision-index parity, nested-agent validation, and mechanics topology
validation. Live registration, invocation, freshness, benefit, and rollback
remain later host/runtime evidence.
