# Historical Mechanics Outside The Current Tree

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0106
- Original date: 2026-09-04
- Surface classes: mechanics, provenance, validation, agent guidance
- SDK facets: mechanics topology, validation
- Mechanic parents: runtime-seam, boundary-bridge, checkpoint, codex-projection
- Guard families: mechanics topology, agent mesh
- Posture: accepted

## Context

Four mechanics archives retain former-parent route maps surrounded by
historical indexes and instruction scaffolding. The maps still protect
current topology: former parent names must not reappear as active parents,
and every replacement must resolve to a current part. The surrounding
historical files do not need to be present for that protection.

## Decision

Retire the four package-local `legacy/` trees from the ordinary checkout.
Keep each unchanged `former-routes.json` payload directly in its package,
registered by `mechanics/topology.json#former_route_manifests`. Preserve its
schema and old-name/current-route validation. Remove only archive scaffolding
presence obligations and the cards that apply exclusively to removed files.

`PROVENANCE.md` remains the active-to-history bridge. Historical explanation
uses immutable Git references; current work uses active packages and parts.
There is no replacement archive district, service, or runtime. Importable SDK
APIs, routing policy, checkpoint lifecycle, and owner boundaries do not change.

This supersedes the requirement to store former-route accounting inside
package `legacy/` directories, not the prior decisions' recorded rationale or
their prohibition on restoring former names as active topology.

## Recovery

The exact source commit is `4ea7e3bc8fb63d2ebbf531ee0f763a56a9d5fd43`.
All 24 tracked files in these subtrees were verified at that commit before
retirement; four route-map payloads are also retained unchanged locally.

| Former subtree | Historical source | Current map |
| --- | --- | --- |
| `mechanics/runtime-seam/legacy/` | [Snapshot](https://github.com/8Dionysus/aoa-sdk/tree/4ea7e3bc8fb63d2ebbf531ee0f763a56a9d5fd43/mechanics/runtime-seam/legacy) | `mechanics/runtime-seam/former-routes.json` |
| `mechanics/boundary-bridge/legacy/` | [Snapshot](https://github.com/8Dionysus/aoa-sdk/tree/4ea7e3bc8fb63d2ebbf531ee0f763a56a9d5fd43/mechanics/boundary-bridge/legacy) | `mechanics/boundary-bridge/former-routes.json` |
| `mechanics/checkpoint/legacy/` | [Snapshot](https://github.com/8Dionysus/aoa-sdk/tree/4ea7e3bc8fb63d2ebbf531ee0f763a56a9d5fd43/mechanics/checkpoint/legacy) | `mechanics/checkpoint/former-routes.json` |
| `mechanics/codex-projection/legacy/` | [Snapshot](https://github.com/8Dionysus/aoa-sdk/tree/4ea7e3bc8fb63d2ebbf531ee0f763a56a9d5fd43/mechanics/codex-projection/legacy) | `mechanics/codex-projection/former-routes.json` |

Recover any file with `git show <full-source-commit>:<original-path>`.
Historical relative links resolve within that same tree. Ordinary validation
does not fetch history or reconstruct the removed archive.

## Consequences

The active tree contains the small checked compatibility maps, not a second
historical instruction mesh. Generated decision and source-topology indexes
must be regenerated from their authored sources. A green topology check
does not establish runtime activation, release, or owner acceptance.
